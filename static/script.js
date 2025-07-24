// ~/static/script.js

// Main frontend script for Enhanced Domain Intelligence Analyzer.
// Handles session management, chat, file upload, UI updates, and API communication.

let sessions = [];
let currentSessionId = null;
let currentSessionName = "";
let currentModel = "groq";
let isWaiting = false;
let currentSessionType = "domain"; // "domain" or "document"
let documentStatus = null; // Store document session info

const AVAILABLE_MODELS = {
    groq: [
        { value: "llama3-8b-8192", label: "Llama 3 8B (Groq)" }
    ],
    local: [
        { value: "local", label: "Local GGUF Model" }
    ]
};

// Initialize UI and event handlers on page load
document.addEventListener("DOMContentLoaded", () => {
    setupSessionUI();
    setupModelToggle();
    setupAnalyzeButtons();
    setupChatForm();
    setupSidebarFooter();
    loadSessions(); // Initial load
    updateHeader();
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (sidebar && toggleBtn) {
        toggleBtn.onclick = () => {
            sidebar.classList.toggle('collapsed');
        };
    }
});

// Session UI setup
function setupSessionUI() {
    document.getElementById("new-session-btn").onclick = () => {
        createSession("New Session", currentModel);
    };
}

// Model toggle setup
function setupModelToggle() {
    const modelToggle = document.getElementById("model-toggle");
    if (modelToggle) {
        modelToggle.value = currentModel;
        modelToggle.onchange = () => {
            currentModel = modelToggle.value;
            updatePoweredBy();
        };
    } else {
        console.error("Element with ID 'model-toggle' not found.");
    }
}

// Analyze buttons setup
function setupAnalyzeButtons() {
    document.getElementById("analyze-domain-btn").onclick = () => {
        document.getElementById("chat-input").value = "Enter domain to analyze (e.g., example.com): ";
        document.getElementById("chat-input").focus();
    };
    document.getElementById("analyze-urls-btn").onclick = () => {
        document.getElementById("chat-input").value = "Enter URLs to analyze (comma separated): ";
        document.getElementById("chat-input").focus();
    };
    const analyzeFilesBtn = document.getElementById("analyze-files-btn");
    if (analyzeFilesBtn) {
        analyzeFilesBtn.onclick = () => {
            document.getElementById("file-input").click();
        };
    } else {
        console.error("Element with ID 'analyze-files-btn' not found.");
    }

    const fileInput = document.getElementById("file-input");
    if (fileInput) {
        fileInput.onchange = function() {
            if (!currentSessionId) {
                appendMessage("assistant", "❌ Please create or select a session first.");
                this.value = "";
                return;
            }
            const files = this.files;
            if (!files.length) return;

            // Filter out temporary Word files
            const filesToUpload = Array.from(files).filter(file => !file.name.startsWith("~$"));

            if (filesToUpload.length === 0) {
                appendMessage("assistant", " No valid files selected for upload (temporary files were filtered out).");
                this.value = "";
                return;
            }

            for (let i = 0; i < filesToUpload.length; i++) {
                uploadAndAnalyzeFile(filesToUpload[i]);
            }
            this.value = ""; // Clear the input after processing
        };
    } else {
        console.error("Element with ID 'file-input' not found.");
    }
}

// Chat form setup
function setupChatForm() {
    document.getElementById("chat-form").onsubmit = e => {
        e.preventDefault();
        if (!currentSessionId || isWaiting) return;
        const input = document.getElementById("chat-input");
        const msg = input.value.trim();
        if (!msg) return;

        if (msg.startsWith("Enter domain to analyze")) {
            const domain = msg.replace(/^Enter domain to analyze.*?:\s*/i, '').trim();
            if (domain) analyzeDomain(domain);
            input.value = "";
            return;
        }
        if (msg.startsWith("Enter URLs to analyze")) {
            const urls = msg.replace(/^Enter URLs to analyze.*?:\s*/i, '').split(",").map(u => u.trim()).filter(Boolean);
            if (urls.length) analyzeUrls(urls);
            input.value = "";
            return;
        }

        appendMessage("user", msg);
        input.value = "";
        sendChat(msg);
    };
}

// Sidebar footer setup
function setupSidebarFooter() {
    document.getElementById("settings-btn").onclick = showDiagnostics;
    document.getElementById("sync-btn").onclick = () => {
        if (currentSessionId) syncSession();
    };
    document.getElementById("clear-chat-btn").onclick = () => {
        if (currentSessionId) clearChat();
    };
    
    // Add document clear button functionality
    const clearDocsBtn = document.getElementById("clear-docs-btn");
    if (clearDocsBtn) {
        clearDocsBtn.onclick = () => {
            if (currentSessionId) clearDocuments();
        };
    }
}

function selectSession(sessionId) {
    console.log("Attempting to select session:", sessionId);
    const sess = sessions.find(s => s.id === sessionId);
    if (!sess) {
        console.error("Session not found:", sessionId);
        // If a session is not found, it might have been deleted.
        // loadSessions will handle re-selecting a valid session.
        loadSessions(); // Re-load sessions to ensure UI is consistent
        return;
    }

    console.log("Found session:", sess.name, "Current session:", currentSessionId);
    
    // Always update currentSessionId and currentSessionName
    currentSessionId = sessionId;
    currentSessionName = sess.name;

    console.log("Updated current session to:", currentSessionId, currentSessionName);

    // Add a visual feedback message
    appendMessage("assistant", `🔄 Switched to session: ${sess.name}`);

    updateHeader();
    renderSessionList(); // Re-render to highlight the newly active session

    // Always clear and load history for the selected session
    clearChatHistory();
    loadChatHistory();
    
    // Load document status for the new session (this will update session type)
    loadDocumentStatus();
    
    console.log("Session selection completed for:", sessionId);
}


function createSession(name, provider) {
    isWaiting = true;
    fetch("/api/initialize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, provider })
    })
    .then(r => r.json())
    .then(data => {
        isWaiting = false;
        if (data.success) {
            // After creating, load sessions to get the new session in the list
            // then select it.
            loadSessions(() => {
                selectSession(data.session_id);
            });
        } else {
            appendMessage("assistant", `❌ Error creating session: ${data.message}`);
        }
    })
    .catch(error => {
        isWaiting = false;
        console.error("Create session error:", error);
        appendMessage("assistant", `❌ Error creating session: ${error.message || ''}`);
    });
}

function deleteSession(sessionId) {
    if (sessionId === currentSessionId) {
        const currentIndex = sessions.findIndex(s => s.id === sessionId);
        let newSessionToSelectId = null;
        if (sessions.length > 1) {
            // Select the next session in the list, or the previous if it's the last one
            newSessionToSelectId = sessions[(currentIndex + 1) % sessions.length].id;
            if (newSessionToSelectId === sessionId) { // Edge case: only one session left and it's being deleted
                newSessionToSelectId = null;
            }
        }

        fetch(`/api/session/${sessionId}`, { method: "DELETE" })
            .then(() => {
                loadSessions(() => { // Reload sessions after deletion
                    if (newSessionToSelectId && sessions.some(s => s.id === newSessionToSelectId)) {
                        selectSession(newSessionToSelectId);
                    } else if (sessions.length > 0) {
                        selectSession(sessions[0].id); // Fallback to first session
                    } else {
                        createSession("New Session", currentModel); // Create new if no sessions left
                    }
                });
            })
            .catch(error => {
                console.error("Delete session error:", error);
                appendMessage("assistant", `❌ Error deleting session: ${error.message || ''}`);
            });
    } else {
        fetch(`/api/session/${sessionId}`, { method: "DELETE" })
            .then(() => loadSessions()) // Just reload sessions if not current
            .catch(error => {
                console.error("Delete session error:", error);
                appendMessage("assistant", `❌ Error deleting session: ${error.message || ''}`);
            });
    }
}



// Other functions...

function loadSessions(callback) {
    fetch("/api/sessions")
        .then(r => r.json())
        .then(data => {
            sessions = data.sessions || [];
            renderSessionList();

            let sessionToActivateId = null;

            // 1. Try to re-activate the previously active session if it still exists
            if (currentSessionId && sessions.some(s => s.id === currentSessionId)) {
                sessionToActivateId = currentSessionId;
            }
            // 2. If no previous session, or it was deleted, activate the first available session
            else if (sessions.length > 0) {
                sessionToActivateId = sessions[0].id;
            }
            // 3. If no sessions exist, create a new one
            else {
                // This will trigger another loadSessions call, so we exit this one.
                createSession("New Session", currentModel);
                if (callback) callback();
                return;
            }

            // Only call selectSession if a session is determined to be activated
            // This prevents redundant calls if the session is already active and correctly set.
            if (sessionToActivateId && sessionToActivateId !== currentSessionId) {
                selectSession(sessionToActivateId);
            } else if (sessionToActivateId && sessionToActivateId === currentSessionId) {
                // If the session is already active and correctly set, just ensure UI is updated
                renderSessionList();
                updateHeader(); // Ensure header is correct
            }


            if (callback) callback(); // Execute callback after sessions are loaded
            // updateHeader(); // Moved inside selectSession or the else if block above
        })
        .catch(error => {
            console.error("Load sessions error:", error);
            appendMessage("assistant", `❌ Error loading sessions: ${error.message || ''}`);
        });
}

// Add a refresh button functionality
document.getElementById("refresh-btn").onclick = () => {
    loadSessions(); // Call this function when the refresh button is clicked
    // loadChatHistory(); // No need to call directly, selectSession will handle it
};

function loadChatHistory() {
    if (!currentSessionId) {
        console.warn("loadChatHistory called with no currentSessionId.");
        return;
    }

    fetch(`/api/history/${currentSessionId}`)
        .then(r => {
            if (!r.ok) { // Check for HTTP errors (e.g., 404, 500)
                return r.text().then(text => { throw new Error(`HTTP error! status: ${r.status}, response: ${text}`); });
            }
            return r.json();
        })
        .then(data => {
            clearChatHistory();
            (data.history || []).forEach(msg => appendMessage(msg.role, msg.content));
        })
        .catch(error => {
            console.error("Load chat history error:", error);
            appendMessage("assistant", `❌ Error loading chat history: ${error.message || ''}`);
        });
}

function appendMessage(role, content) {
    const chat = document.getElementById("chat-history");
    if (!chat) return;
    const div = document.createElement("div");
    div.className = `message ${role}`;
    // Convert newlines to <br> for HTML rendering
    const htmlContent = content.replace(/\n/g, '<br>');
    div.innerHTML = htmlContent;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function clearChatHistory() {
    const chat = document.getElementById("chat-history");
    if (chat) {
        chat.innerHTML = "";
    }
}

function updateHeader() {
    const sessionTitleElement = document.getElementById("session-title");
    if (sessionTitleElement) {
        sessionTitleElement.textContent = currentSessionName || "New Session";
    } else {
        console.error("Element with ID 'session-title' not found.");
    }
    updatePoweredBy();
}

function updatePoweredBy() {
    const banner = document.getElementById("powered-by-banner");
    if (banner) {
        banner.textContent = currentModel === "groq"
            ? "Powered by Llama 3 8B (Groq)"
            : "Powered by Local GGUF Model";
    } else {
        console.error("Element with ID 'powered-by-banner' not found.");
    }
}

function renderSessionList() {
    const list = document.getElementById("session-list");
    if (!list) {
        console.error("Element with ID 'session-list' not found.");
        return;
    }
    list.innerHTML = "";

    sessions.forEach(sess => {
        const li = document.createElement("li");
        li.className = sess.id === currentSessionId ? "active" : "";
        
        // Create session name span
        const sessionNameSpan = document.createElement("span");
        sessionNameSpan.className = "session-name";
        sessionNameSpan.textContent = sess.name;
        sessionNameSpan.onclick = () => selectSession(sess.id);
        
        // Create delete button
        const deleteBtn = document.createElement("i");
        deleteBtn.className = "delete-session-btn bi bi-file-earmark-x ";
        deleteBtn.onclick = (event) => {
            event.stopPropagation();
            deleteSession(sess.id);
        };
        
        // Add click handler to the entire li element as well
        li.onclick = () => selectSession(sess.id);
        
        // Append elements
        li.appendChild(sessionNameSpan);
        li.appendChild(deleteBtn);
        list.appendChild(li);
    });
}

function sendChat(msg) {
    isWaiting = true;
    setSendButtonState(false);

    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant typing";
    typingDiv.textContent = "Assistant is typing...";
    typingDiv.id = "typing-indicator";
    document.getElementById("chat-history").appendChild(typingDiv);
    document.getElementById("chat-history").scrollTop = document.getElementById("chat-history").scrollHeight;

    // Determine chat type based on session type
    const chatType = currentSessionType === "document" ? "document" : "auto";

    fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            session_id: currentSessionId, 
            message: msg,
            chat_type: chatType
        })
    })
    .then(r => r.json())
    .then(data => {
        removeTypingIndicator();
        setSendButtonState(true);
        isWaiting = false;
        
        if (data.success && data.response) {
            let responseContent = data.response;
            
            // Add sources if available (for document chat)
            // if (data.sources && data.sources.length > 0) {
            //     responseContent += "\n\n Sources:\n";
            //     data.sources.forEach(source => {
            //         responseContent += `- ${source}\n`;
            //     });
            // }
            
            appendMessage("assistant", responseContent);
        } else if (!data.success) {
            appendMessage("assistant", `❌ Error: ${data.message || "Failed to get response."}`);
        }
    })
    .catch(error => {
        removeTypingIndicator();
        setSendButtonState(true);
        isWaiting = false;
        console.error("Chat error:", error);
        appendMessage("assistant", `❌ Error: Could not get response. ${error.message || ''}`);
    });
}

function setSendButtonState(enabled) {
    const sendButton = document.querySelector("#chat-form button[type=submit]");
    if (sendButton) {
        sendButton.disabled = !enabled;
    }
}

function removeTypingIndicator() {
    const typing = document.getElementById("typing-indicator");
    if (typing) typing.remove();
}

function analyzeDomain(domain) {
    appendMessage("user", `Analyze domain: ${domain}`);

    // Show typing indicator before starting analysis
    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant typing";
    typingDiv.textContent = "Analyzing domain...";
    typingDiv.id = "typing-indicator";
    document.getElementById("chat-history").appendChild(typingDiv);
    document.getElementById("chat-history").scrollTop = document.getElementById("chat-history").scrollHeight;

    fetch("/api/analyze_domain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId, domain })
    })
    .then(r => r.json())
    .then(data => {
        removeTypingIndicator();
        // if (data.summary) appendMessage("assistant", `<pre>${data.summary}</pre>`);
        // if (data.report) appendMessage("assistant", `<pre>${data.report}</pre>`);
        if (data.content) appendMessage("assistant", `<pre>${data.content}</pre>`);
        if (!data.success && data.message) appendMessage("assistant", `❌ Error: ${data.message}`);
    })
    .catch(error => {
        removeTypingIndicator();
        console.error("Analyze domain error:", error);
        appendMessage("assistant", `❌ Error analyzing domain: ${error.message || ''}`);
    });
}

function analyzeUrls(urls) {
    appendMessage("user", `Analyze URLs: ${urls.join(", ")}`);

    // Show typing indicator before starting analysis
    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant typing";
    typingDiv.textContent = "Analyzing URLs...";
    typingDiv.id = "typing-indicator";
    document.getElementById("chat-history").appendChild(typingDiv);
    document.getElementById("chat-history").scrollTop = document.getElementById("chat-history").scrollHeight;

    fetch("/api/analyze_urls", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId, urls })
    })
    .then(r => r.json())
    .then(data => {
        removeTypingIndicator();
        if (data.content) appendMessage("assistant", `<pre>${data.content}</pre>`);
        if (!data.success && data.message) appendMessage("assistant", `❌ Error: ${data.message}`);
    })
    .catch(error => {
        removeTypingIndicator();
        console.error("Analyze URLs error:", error);
        appendMessage("assistant", `❌ Error analyzing URLs: ${error.message || ''}`);
    });
}

function syncSession() {
    appendMessage("assistant", "Syncing...");
    fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId })
    })
    .then (r => r.json())
    .then(data => {
        if (data.result) appendMessage("assistant", `<pre>${data.result}</pre>`);
        if (!data.success && data.message) appendMessage("assistant", `❌ Error: ${data.message}`);
    })
    .catch(error => {
        console.error("Sync error:", error);
        appendMessage("assistant", `❌ Error syncing: ${error.message || ''}`);
    });
}

function clearChat() {
    fetch("/api/clear-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId })
    })
    .then(r => r.json())
    .then(() => {
        clearChatHistory();
        appendMessage("assistant", " Chat history cleared.");
    })
    .catch(error => {
        console.error("Clear chat error:", error);
        appendMessage("assistant", `❌ Error clearing chat: ${error.message || ''}`);
    });
}

function showDiagnostics() {
    Promise.all([
        fetch("/api/status").then(r => r.json()),
        fetch("/api/load_model", { method: "POST" }).then(r => r.json())
    ]).then(([status, load]) => {
        appendMessage("assistant", `<pre>Status: ${JSON.stringify(status, null, 2)}</pre>`);
        appendMessage("assistant", `<pre>Load Model: ${JSON.stringify(load, null, 2)}</pre>`);
    })
    .catch(error => {
        console.error("Diagnostics error:", error);
        appendMessage("assistant", `❌ Error fetching diagnostics: ${error.message || ''}`);
    });
}

function uploadAndAnalyzeFile(file) {
    appendMessage("user", ` Uploading file: ${file.name}`);
    // appendMessage("assistant", " Processing document...");
    // Show typing indicator before starting analysis
    const typingDiv = document.createElement("div");
    typingDiv.className = "message assistant typing";
    typingDiv.textContent = "Processing document...";
    typingDiv.id = "typing-indicator";
    document.getElementById("chat-history").appendChild(typingDiv);
    document.getElementById("chat-history").scrollTop = document.getElementById("chat-history").scrollHeight;
    
    // Validate file size (50MB limit)
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
    if (file.size > MAX_FILE_SIZE) {
        appendMessage("assistant", `❌ Error: File too large. Maximum size is 50MB.`);
        return;
    }
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", currentSessionId);

    fetch("/api/upload_file", {
        method: "POST",
        body: formData
    })
    .then(r => {
        if (!r.ok) {
            throw new Error(`HTTP error! status: ${r.status}`);
        }
        return r.json();
    })
    .then(data => {
        if (data.success) {
            removeTypingIndicator();
            appendMessage("assistant", ` ${data.message}`);
            if (data.files_processed) {
                appendMessage("assistant", ` Total chunks added: ${data.chunks_added}`);
                appendMessage("assistant", ` Now you can ask questions about the file.`);
            }
            
            // Update session type to document
            currentSessionType = "document";
            updateSessionTypeIndicator();
            
            // Update session name if it's generic
            if (currentSessionName === "New Session" || currentSessionName.startsWith("Untitled Session")) {
                currentSessionName = `Document Session`;
                updateHeader();
                const sess = sessions.find(s => s.id === currentSessionId);
                if (sess) {
                    sess.name = currentSessionName;
                    renderSessionList();
                }
            }
            
            // Load document status
            loadDocumentStatus();
            
        } else {
            appendMessage("assistant", `❌ Error: ${data.message || "Failed to process file."}`);
        }
    })
    .catch(error => {
        removeTypingIndicator();
        console.error("Upload and analyze file error:", error);
        appendMessage("assistant", `❌ Error: Failed to process file: ${error.message || ''}`);
    });
}

function loadDocumentStatus() {
    if (!currentSessionId) return;
    
    fetch(`/api/document_status/${currentSessionId}`)
        .then(r => r.json())
        .then(data => {
            if (data.success && data.data) {
                documentStatus = data.data;
                updateDocumentStatusDisplay();
                
                // Update session type based on document status
                if (documentStatus && documentStatus.total_chunks > 0) {
                    currentSessionType = "document";
                } else {
                    currentSessionType = "domain";
                }
                updateSessionTypeIndicator();
            } else {
                // Reset to domain type if no document data
                documentStatus = null;
                currentSessionType = "domain";
                updateDocumentStatusDisplay();
                updateSessionTypeIndicator();
            }
        })
        .catch(error => {
            console.error("Load document status error:", error);
            // Reset to domain type on error
            documentStatus = null;
            currentSessionType = "domain";
            updateDocumentStatusDisplay();
            updateSessionTypeIndicator();
        });
}

function updateDocumentStatusDisplay() {
    const statusContainer = document.getElementById("document-status");
    if (!statusContainer || !documentStatus) return;
    
    if (documentStatus.total_chunks > 0) {
        statusContainer.innerHTML = `
            <div class="document-info">
                <span class="doc-icon">📄</span>
                <span class="doc-count">${documentStatus.documents_processed.length} documents</span>
                <span class="chunk-count">${documentStatus.total_chunks} chunks</span>
            </div>
        `;
        statusContainer.style.display = "block";
    } else {
        statusContainer.style.display = "none";
    }
}

function updateSessionTypeIndicator() {
    const typeIndicator = document.getElementById("session-type-indicator");
    if (!typeIndicator) return;
    
    if (currentSessionType === "document") {
        typeIndicator.textContent = "Document Analysis";
        typeIndicator.className = "bi bi-folder session-type document";
    } else {
        typeIndicator.textContent = "Domain Analysis";
        typeIndicator.className = "bi bi-globe session-type domain";
    }
}

function clearDocuments() {
    if (!currentSessionId) return;
    
    appendMessage("assistant", " Clearing all documents...");
    
    fetch(`/api/clear_documents/${currentSessionId}`, {
        method: "POST"
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            appendMessage("assistant", `✅ ${data.message}`);
            documentStatus = null;
            currentSessionType = "domain";
            updateDocumentStatusDisplay();
            updateSessionTypeIndicator();
        } else {
            appendMessage("assistant", `❌ Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error("Clear documents error:", error);
        appendMessage("assistant", `❌ Error clearing documents: ${error.message || ''}`);
    });
}
