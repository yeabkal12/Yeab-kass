// frontend/app.js (Final Version with Correct API URL)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const gameList = document.getElementById('game-list');
    
    // --- CRITICAL FIX ---
    // We now use the FULL, absolute URL of your BACKEND API service.
    // Make sure this is the URL of your Python Web Service, NOT your Static Site.
    const API_URL = 'https://yeab-game-zone-api.onrender.com/api/games'; // <-- Double-check this is your API's URL

    function fetchGames() {
        gameList.innerHTML = '<p>Loading open games...</p>';
        fetch(API_URL) // <-- Use the full URL
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // ... (The rest of the function remains exactly the same)
            })
            .catch(error => {
                console.error('Error fetching games:', error);
                // Show a more helpful error message
                gameList.innerHTML = `<p>Error: Could not connect to the game server. Please try again later.</p>`;
            });
    }

    // ... (The rest of the file and all its event listeners remain the same)
});