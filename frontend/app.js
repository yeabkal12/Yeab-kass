// frontend/app.js (Complete Frontend Code - UPDATED)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- 1. CRITICAL: THIS URL HAS BEEN UPDATED ---
    // The frontend will now fetch data from your new backend URL.
    const API_URL = 'https://yeab-kass-1.onrender.com/api/games';

    // --- 2. Robust Element Finding Utility ---
    const getEl = (id) => document.getElementById(id);

    const loadingView = getEl('loading-view');
    const appContainer = getEl('app-container');
    const createGameView = getEl('create-game-view');
    const gameList = getEl('game-list');
    const newGameBtn = getEl('new-game-btn');
    const refreshBtn = getEl('refresh-btn');
    const cancelCreateBtn = getEl('cancel-create-btn');

    // --- 3. View Management Function ---
    function showView(view) {
        if (!view) return; // Prevent errors if a view is missing
        // Hide all major views first
        if (loadingView) loadingView.classList.add('hidden');
        if (appContainer) appContainer.classList.add('hidden');
        if (createGameView) createGameView.classList.add('hidden');
        // Show the requested view
        view.classList.remove('hidden');
    }

    // --- 4. Core Logic with Bulletproof Error Handling ---
    function fetchGames() {
        showView(loadingView); // Show loading spinner immediately

        fetch(API_URL)
            .then(response => {
                // Check if the server responded with a success status code
                if (!response.ok) {
                    // Create a detailed error to be caught by the .catch block
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                // If response is OK, parse it as JSON
                return response.json();
            })
            .then(data => {
                if (!gameList) return; // Don't proceed if the game list element doesn't exist

                gameList.innerHTML = ''; // Clear previous list
                if (data.games && data.games.length > 0) {
                    data.games.forEach(game => {
                        const card = document.createElement('div');
                        card.className = 'game-card';
                        card.innerHTML = `
                            <div class="card-player">
                                <div class="avatar-container">
                                    <img src="${game.creator_avatar}" alt="Avatar">
                                    <span class="star-badge">⭐</span>
                                </div>
                                <span class="username">${game.creator_name || 'Anonymous'}</span>
                                <span class="user-stake">${game.stake} ብር</span>
                            </div>
                            <div class="card-info">
                                <!-- Placeholder for win condition text -->
                                <p class="win-condition-text">Be the first to score 2 crowns!</p>
                                <button class="join-btn" data-game-id="${game.id}">Join Game</button>
                            </div>
                            <div class="card-stats">
                                <div class="game-stat"><span>Stake</span><strong>${game.stake} ብር</strong></div>
                                <div class="game-stat"><span>Prize</span><strong class="prize-amount">${game.prize} ብር</strong></div>
                            </div>`;
                        gameList.appendChild(card);
                    });
                } else {
                    gameList.innerHTML = '<p class="empty-list-message">No open games found. Create one!</p>';
                }
                showView(appContainer); // Show the main view with the populated list
            })
            .catch(error => {
                // This block will catch network errors AND the server errors we threw above
                console.error('CRITICAL FETCH ERROR:', error);
                
                // Show a user-friendly alert via Telegram's UI
                tg.showAlert(`Could not connect to the game server. Please check your internet connection and try again.\n\nError: ${error.message}`);
                
                // Update the UI to show a helpful error message
                showView(appContainer);
                if (gameList) {
                    gameList.innerHTML = `<div class="error-message">
                                            <p>Could not load games.</p>
                                            <p>Please tap the Refresh button to try again.</p>
                                          </div>`;
                }
            });
    }

    // --- 5. Event Listeners (with safety checks) ---
    if (newGameBtn) newGameBtn.addEventListener('click', () => showView(createGameView));
    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', () => showView(appContainer));
    if (refreshBtn) refreshBtn.addEventListener('click', fetchGames);

    // Add a listener to the game list for join buttons (using event delegation)
    if (gameList) {
        gameList.addEventListener('click', (event) => {
            if (event.target && event.target.classList.contains('join-btn')) {
                const gameId = event.target.dataset.gameId;
                tg.sendData(`join_game_${gameId}`);
                tg.close();
            }
        });
    }

    // --- 6. Initial Load ---
    fetchGames();
});