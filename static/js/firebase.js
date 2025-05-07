console.log("🚀 Chatbot.js Loaded! Initializing...");

// ✅ Initialize Firebase
const firebaseConfig = {
    apiKey: "AIzaSyBv1GiiaTh3ShI6G2lFzMI3NeAH8KCdcxY",
    authDomain: "finperson-6ab9f.firebaseapp.com",
    projectId: "finperson-6ab9f",
    storageBucket: "finperson-6ab9f.appspot.com",
    messagingSenderId: "534750910607",
    appId: "1:534750910607:web:634fe86f7b75553686f8fa",
    measurementId: "G-HYHGZVXN9T"
};

// ✅ Fix: Ensure Firebase is Only Initialized Once
if (!window.firebase || !firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
    console.log("✅ Firebase initialized successfully.");
} else {
    console.log("✅ Firebase already initialized.");
}

// ✅ Firebase Authentication & Firestore
const auth = firebase.auth();
const db = firebase.firestore();

// ✅ Sign-In with Google
function signInWithGoogle() {
    let provider = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(provider)
        .then(result => {
            document.getElementById("userStatus").innerText = `Signed in as: ${result.user.displayName}`;
            loadChatHistory();
        })
        .catch(error => {
            console.error("🚨 Sign-in error:", error);
        });
}

// ✅ Sign Out
function signOut() {
    auth.signOut().then(() => {
        document.getElementById("userStatus").innerText = "Not signed in";
    });
}

// ✅ Load Chat History
async function loadChatHistory() {
    let user = auth.currentUser;
    let persona = document.body.getAttribute("data-persona");

    if (!user) {
        console.warn("⚠️ User not signed in. Chat history will not be loaded.");
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

// ✅ Detect Authentication State
auth.onAuthStateChanged(user => {
    if (user) {
        document.getElementById("userStatus").innerText = `Signed in as: ${user.displayName}`;
        loadChatHistory();
    } else {
        document.getElementById("userStatus").innerText = "Not signed in";
    }
});

// ✅ Send Message
async function sendMessage() {
    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (message === "") return;

    input.value = "";  // Clear input field

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<p class="message user-message">${message}</p>`;
    chatbox.scrollTop = chatbox.scrollHeight;

    document.getElementById("sendSound").play(); // Play send sound

    let typingIndicator = document.querySelector(".typing-indicator");
    typingIndicator.style.display = "block"; // Show typing indicator

    // ✅ Fix: Ensure persona is set correctly
    let persona = document.body.getAttribute("data-persona") || 
                  document.getElementById("chatbox").getAttribute("data-persona");

    if (!persona || persona === "null") {
        console.error("🚨 Error: Persona is missing.");
        alert("Error: Chatbot persona is missing. Please refresh the page.");
        return;
    }

    let userId = auth.currentUser ? auth.currentUser.uid : "anonymous";

    console.log(`📤 Sending Message: "${message}" to Persona: ${persona}`);

    let response = await fetch(`/chat_api/${persona}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, user_id: userId })
    });

    let data = await response.json();
    typingIndicator.style.display = "none"; // Hide typing indicator

    setTimeout(() => {
        chatbox.innerHTML += `<p class="message bot-message">${data.response}</p>`;
        chatbox.scrollTop = chatbox.scrollHeight;
        document.getElementById("receiveSound").play(); // Play receive sound
    }, 1000); // Simulate typing delay
}

// ✅ Handle "Enter" Key Press
function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
}

console.log("🚀 Chatbot Ready!");
