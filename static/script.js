const SERVER_URL = "http://127.0.0.1:8080";

document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript Loaded");

    const chatInput = document.getElementById("user-input");
    const chatSendButton = document.querySelector("#chat-input button");
    const chatBox = document.getElementById("chat-box");
    const tradeActionInput = document.getElementById("trade-action");
    const tradeSubmitButton = document.querySelector("#trading-game button");

    if (chatSendButton) {
        chatSendButton.addEventListener("click", sendChatMessage);
    } else {
        console.error("Chat button not found!");
    }

    if (tradeSubmitButton) {
        tradeSubmitButton.addEventListener("click", sendTradeAction);
    } else {
        console.error("Trade button not found!");
    }
});

function playSound() {
    document.getElementById("clickSound").play();
}

function showTypingIndicator() {
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "typing-indicator";
    typingIndicator.innerText = "AI is typing...";
    typingIndicator.id = "typing-indicator";
    document.getElementById("chat-box").appendChild(typingIndicator);
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById("typing-indicator");
    if (typingIndicator) typingIndicator.remove();
}

async function sendChatMessage() {
    const userInput = document.getElementById("user-input").value;
    if (!userInput.trim()) return;

    appendMessage("You", userInput, "user-message");
    document.getElementById("user-input").value = "";
    showTypingIndicator();

    try {
        const response = await fetch(`${SERVER_URL}/chatbot`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "Guest", message: userInput })
        });

        const data = await response.json();
        removeTypingIndicator();
        appendMessage("AI", data.response, "ai-message");
    } catch (error) {
        removeTypingIndicator();
        appendMessage("AI", "⚠️ Error connecting to server.", "error-message");
    }
}

async function sendTradeAction() {
    const tradeAction = document.getElementById("trade-action").value;
    if (!tradeAction.trim()) return;

    document.getElementById("trade-feedback").innerText = "Processing trade...";

    try {
        const response = await fetch(`${SERVER_URL}/trading-game`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: "Guest", trade_action: tradeAction, balance: 5000 })
        });

        const data = await response.json();
        document.getElementById("trade-feedback").innerText = data.response;
    } catch (error) {
        document.getElementById("trade-feedback").innerText = "⚠️ Error processing trade.";
    }
}

function appendMessage(sender, message, className) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.className = className;

    if (sender === "AI") {
        const copyButton = document.createElement("button");
        copyButton.className = "copy-button";
        copyButton.innerText = "📋";
        copyButton.onclick = () => copyToClipboard(message);
        messageElement.appendChild(copyButton);
    }

    const messageContent = document.createElement("span");
    messageContent.innerText = message;
    messageElement.appendChild(messageContent);

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied to clipboard!");
    }).catch(err => {
        console.error("Failed to copy: ", err);
    });
}