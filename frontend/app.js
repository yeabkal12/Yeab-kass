// frontend/app.js (Final Version with Full API URL)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const gameList = document.getElementById('game-list');
    
    // --- CRITICAL FIX ---
    // We now use the FULL, absolute URL of your backend API service.
    const API_URL = 'https://yeab-game-zone-api.onrender.com/api/games'; // <-- Replace with your API service name if different

    function fetchGames() {
        gameList.innerHTML = '<p>Loading open games...</p>';
        fetch(API_URL) // <-- Use the full URL
            .then(response => response.json())
            .then(data => {
                // ... (The rest of the function remains exactly the same)
            })
            .catch(error => {
                // ... (The error handling remains the same)
            });
    }

    // ... (The rest of the file and all its event listeners remain the same)
});