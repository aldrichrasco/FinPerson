let userId = "anonymous"; // Default to anonymous if not signed in

// Initialize Firebase Authentication
function initializeFirebase() {
    if (typeof firebase === "undefined") {
        console.error("❌ Firebase SDK failed to load.");
        return;
    }

    const firebaseConfig = {
        apiKey: "AIzaSyBv1GiiaTh3ShI6G2lFzMI3NeAH8KCdcxY",
        authDomain: "finperson-6ab9f.firebaseapp.com",
        projectId: "finperson-6ab9f",
        storageBucket: "finperson-6ab9f.appspot.com",
        messagingSenderId: "534750910607",
        appId: "1:534750910607:web:634fe86f7b75553686f8fa",
        measurementId: "G-HYHGZVXN9T"
    };

    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
        console.log("✅ Firebase initialized successfully.");
    }

    auth = firebase.auth();

    auth.onAuthStateChanged(user => {
        if (user) {
            userId = user.uid;  // Store the user ID
            document.getElementById("userStatus").innerText = `Signed in as: ${user.displayName}`;
        } else {
            userId = "anonymous";  // Reset to anonymous if user signs out
            document.getElementById("userStatus").innerText = "Not signed in";
        }
    });
}

// Sign in with Google
function signInWithGoogle() {
    let provider = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(provider).then(result => {
        userId = result.user.uid; // Store the user ID when signed in
        document.getElementById("userStatus").innerText = `Signed in as: ${result.user.displayName}`;
    }).catch(error => {
        console.error("❌ Sign-in error:", error);
    });
}

// Sign out
function signOut() {
    auth.signOut().then(() => {
        userId = "anonymous";  // Reset user ID to anonymous
        document.getElementById("userStatus").innerText = "Not signed in";
    }).catch(error => {
        console.error("❌ Sign-out error:", error);
    });
}

// Send the message and get the response from API
async function sendMessage() {
    let input = document.getElementById("userInput");
    let message = input.value.trim();
    if (!message) return;

    input.value = ""; // Clear the input field
    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<p class='message user-message'>${message}</p>`;
    chatbox.scrollTop = chatbox.scrollHeight;

    document.getElementById("loading").style.display = "block";

    let persona = "default"; // You can dynamically change the persona based on user choice

    // Use the stored user ID (no need to check auth.currentUser every time)
    let response = await fetch(`http://127.0.0.1:5000/chat/${persona}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message, user_id: userId })
    });

    let data = await response.json();
    document.getElementById("loading").style.display = "none";
    setTimeout(() => {
        chatbox.innerHTML += `<p class='message bot-message'>${data.response}</p>`;
        chatbox.scrollTop = chatbox.scrollHeight;
    }, 1000);
}

// Call initializeFirebase on page load
window.onload = function () {
    initializeFirebase();
};
