// ✅ Ensure Firebase is Ready Before Running Functions
document.addEventListener("DOMContentLoaded", function () {
    if (!window.auth || !window.db) {
        console.error("Firebase is not initialized yet. Retrying...");
        setTimeout(() => {
            initializeChatFunctions();
        }, 1000);
    } else {
        initializeChatFunctions();
    }
});

function initializeChatFunctions() {
    console.log("Firebase Loaded. Ready to use.");

    // ✅ Google Sign-In
    window.signInWithGoogle = function () {
        let provider = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider)
            .then(result => {
                document.getElementById("userStatus").innerText = `Signed in as: ${result.user.displayName}`;
                loadChatHistory();
            })
            .catch(error => console.error("Sign-in error:", error));
    };

    // ✅ Sign Out
    window.signOut = function () {
        auth.signOut().then(() => {
            document.getElementById("userStatus").innerText = "Not signed in";
        });
    };

    // ✅ Load Chat History After Login
    async function loadChatHistory() {
        let user = auth.currentUser;
        let persona = document.getElementById("chatbox").getAttribute("data-persona");

        if (!user) {
            console.warn("User is not logged in. Chat history will not be loaded.");
            return;
        }

        let response = await fetch(`/chat_history/${persona}?user_id=${user.uid}`);
        let data = await response.json();

        let chatbox = document.getElementById("chatbox");
        chatbox.innerHTML = ""; // Clear chatbox

        data.forEach(chat => {
            chatbox.innerHTML += `<p class="message user-message">${chat.user_message}</p>`;
            chatbox.innerHTML += `<p class="message bot-message">${chat.bot_reply}</p>`;
        });

        chatbox.scrollTop = chatbox.scrollHeight; // Scroll to bottom
    }

    // ✅ Listen for Authentication Changes
    auth.onAuthStateChanged(user => {
        if (user) {
            document.getElementById("userStatus").innerText = `Signed in as: ${user.displayName}`;
            loadChatHistory();
        } else {
            document.getElementById("userStatus").innerText = "Not signed in";
        }
    });
}


function signInWithGoogle() {
    let provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider)
        .then(result => {
            let user = result.user;
            document.getElementById("userStatus").innerText = `Signed in as: ${user.displayName}`;
        })
        .catch(error => {
            console.error("Sign-in error:", error);
        });
}

function signOut() {
    firebase.auth().signOut().then(() => {
        document.getElementById("userStatus").innerText = "Signed out";
    });
}

function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
}

async function sendMessage() {
    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (message === "") return;

    input.value = "";  // Clear input

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<p class="message user-message">${message}</p>`;
    chatbox.scrollTop = chatbox.scrollHeight;

    // ✅ Correctly Fetch the Persona from the Template
    let persona = document.getElementById("chatbox").getAttribute("data-persona");

    let response = await fetch(`/chat_api/${persona}`, {  // ✅ Correct URL format
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    });

    let data = await response.json();
    chatbox.innerHTML += `<p class="message bot-message">${data.response}</p>`;
    chatbox.scrollTop = chatbox.scrollHeight;
}
