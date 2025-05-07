console.log("Initializing Firebase...");

// ✅ Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyBv1GiiaTh3ShI6G2lFzMI3NeAH8KCdcxY",
    authDomain: "finperson-6ab9f.firebaseapp.com",
    projectId: "finperson-6ab9f",
    storageBucket: "finperson-6ab9f.appspot.com",
    messagingSenderId: "534750910607",
    appId: "1:534750910607:web:634fe86f7b75553686f8fa",
    measurementId: "G-HYHGZVXN9T"
};

// ✅ Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

console.log("Firebase Loaded. Ready to use.");

// ✅ Google Sign-In
function signInWithGoogle() {
    const provider = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(provider)
        .then(result => {
            document.getElementById("userStatus").innerText = `Signed in as: ${result.user.displayName}`;
            console.log("User Signed In:", result.user);
            loadChatHistory();
        })
        .catch(error => {
            console.error("Sign-in error:", error);
        });
}

// ✅ Sign Out Function
function signOut() {
    auth.signOut().then(() => {
        document.getElementById("userStatus").innerText = "Not signed in";
        console.log("User Signed Out");
    }).catch(error => {
        console.error("Sign-out error:", error);
    });
}

// ✅ Load Chat History for Authenticated Users
async function loadChatHistory() {
    let user = auth.currentUser;
    let persona = document.getElementById("chatbox").getAttribute("data-persona");

    if (!user) {
        console.warn("User not logged in. Chat history not loaded.");
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

// ✅ Monitor Authentication State Changes
auth.onAuthStateChanged(user => {
    if (user) {
        document.getElementById("userStatus").innerText = `Signed in as: ${user.displayName}`;
        loadChatHistory();
    } else {
        document.getElementById("userStatus").innerText = "Not signed in";
    }
});
