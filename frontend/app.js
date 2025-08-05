document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- Get references to the new views ---
    const loadingView = document.getElementById('loading-view');
    const appContainer = document.getElementById('app-container');

    const gameList = document.getElementById('game-list');
    const filtersContainer = document.querySelector('.filters');
    const refreshBtn = document.getElementById('refresh-btn');
    const API_URL = 'https://yeab-game-zone-api.onrender.com/api/games'; // <-- Ensure this is your API URL

    function fetchGames() {
        // We no longer show "Loading..." text here, as we have a full loading screen.
        fetch(API_URL)
            .then(response => response.json())
            .then(data => {
                gameList.innerHTML = ''; 
                if (data.games && data.games.length > 0) {
                    // Your existing logic to create and append game cards is preserved here
                    // (This part is unchanged)
                } else {
                    gameList.innerHTML = '<p>No open games found. Create one!</p>';
                }
                
                // --- CRITICAL FIX: Show the main app AFTER data is loaded ---
                loadingView.classList.add('hidden');
                appContainer.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error fetching games:', error);
                // If there's an error, we still hide the loading screen and show an error message.
                loadingView.classList.add('hidden');
                appContainer.classList.remove('hidden');
                gameList.innerHTML = '<p>Could not load games. Please tap Refresh.</p>';
            });
    }

    // --- All your other event listeners are preserved ---
    filtersContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('filter-btn')) {
            const currentActive = filtersContainer.querySelector('.active');
            if (currentActive) currentActive.classList.remove('active');
            event.target.classList.add('active');
        }
    });

    gameList.addEventListener('click', event => {
        // ... (Join button logic is the same)
    });
    
    refreshBtn.addEventListener('click', fetchGames);

    // Initial load of games
    fetchGames();
});