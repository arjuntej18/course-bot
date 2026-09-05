
// Controls the Course Bot dashboard and communicates with FastAPI.

const startBtn = document.getElementById("startBtn");
const retryBtn = document.getElementById("retryBtn");
const restartBtn = document.getElementById("restartBtn");
const stopBtn = document.getElementById("stopBtn");

const browserStatus = document.getElementById("browserStatus");
const internetStatus = document.getElementById("internetStatus");
const automationStatus = document.getElementById("automationStatus");

const position = document.getElementById("position");
const duration = document.getElementById("duration");
const checkpoint = document.getElementById("checkpoint");
const message = document.getElementById("message");


function formatTime(seconds) {
    seconds = Number(seconds || 0);

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}


async function getStatus() {
    try {
        const response = await fetch("/status");
        const data = await response.json();

        browserStatus.textContent =
            data.browser_connected ? "Connected" : "Disconnected";

        internetStatus.textContent =
            data.internet_connected ? "Connected" : "Disconnected";

        automationStatus.textContent =
            data.state || "Idle";

        position.textContent =
            formatTime(data.position);

        duration.textContent =
            formatTime(data.duration);

        checkpoint.textContent =
            formatTime(data.last_checkpoint);

        message.textContent =
            data.message || "";

    } catch (error) {
        automationStatus.textContent = "Server unavailable";
        message.textContent = "Cannot connect to backend.";
    }
}


async function startAutomation() {

    startBtn.disabled = true;

    message.textContent =
        "Starting automation...";

    try {

        const response = await fetch(
            "/start",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({})
            }
        );

        const data = await response.json();

        message.textContent =
            data.message || "Start requested.";

    } catch (error) {

        message.textContent =
            "Failed to start automation.";

    } finally {

        setTimeout(() => {
            startBtn.disabled = false;
        }, 2000);
    }
}


async function retryAutomation() {

    message.textContent =
        "Retrying...";

    try {

        const response = await fetch(
            "/retry",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        message.textContent =
            data.message || "Retry requested.";

    } catch (error) {

        message.textContent =
            "Retry failed.";

    }
}


async function restartAutomation() {

    message.textContent =
        "Restarting...";

    try {

        const response = await fetch(
            "/restart",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        message.textContent =
            data.message || "Restart requested.";

    } catch (error) {

        message.textContent =
            "Restart failed.";

    }
}


async function stopAutomation() {

    message.textContent =
        "Stopping...";

    try {

        const response = await fetch(
            "/stop",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        message.textContent =
            data.message || "Stop requested.";

    } catch (error) {

        message.textContent =
            "Stop failed.";

    }
}


startBtn.addEventListener(
    "click",
    startAutomation
);

retryBtn.addEventListener(
    "click",
    retryAutomation
);

restartBtn.addEventListener(
    "click",
    restartAutomation
);

stopBtn.addEventListener(
    "click",
    stopAutomation
);


// Update dashboard every second.
setInterval(
    getStatus,
    1000
);

getStatus();
