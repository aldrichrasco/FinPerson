console.log("Chat.js loaded...");

// ✅ Function to Handle User Input & Send Messages
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

    // ✅ Ensure Persona is Correctly Retrieved
    let persona = document.body.getAttribute("data-persona") || 
                  document.getElementById("chatbox").getAttribute("data-persona");

    if (!persona) {
        console.error("🚨 Error: Persona is null. Check if it's being set correctly.");
        alert("Error: Persona is missing. Try refreshing the page.");
        return;
    }

    let userId = firebase.auth().currentUser ? firebase.auth().currentUser.uid : "anonymous";

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
