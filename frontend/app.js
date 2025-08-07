// frontend/app.js (Complete Frontend Code - FINAL, CORRECTED VERSION)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- 1. CRITICAL FIX: INJECTED YOUR WEB SERVICE URL ---
    // The frontend will now correctly fetch data from your Python backend.
    const API_URL = 'https://yeab-kass.onrender.com/api/games';

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
        if (loadingView) loadingView.classList.add('hidden');
        if (appContainer) appContainer.classList.add('hidden');
        if (createGameView) createGameView.classList.add('hidden');
        view.classList.remove('hidden');
    }

    // --- 4. Core Logic with Bulletproof Error Handling ---
    function fetchGames() {
        showView(loadingView);

        fetch(API_URL)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!gameList) return;

                gameList.innerHTML = ''; // Clear previous list
                if (data.games && data.games.length > 0) {
                    data.games.forEach(game => {
                        const card = document.createElement('div');
                        card.className = 'game-card';
                        card.innerHTML = `
                            <div class="card-player">
                                <div class="avatar-container"><img src="${game.creator_avatar}" alt="Avatar"><span class="star-badge">⭐</span></div>
                                <span class="username">${game.creator_name || 'Anonymous'}</span><span class="user-stake">${game.stake} ብር</span>
                            </div>
                            <div class="card-info">
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
                showView(appContainer);
            })
            .catch(error => {
                console.error('CRITICAL FETCH ERROR:', error);
                tg.showAlert(`Could not connect to the game server. Please check your internet connection and try again.\n\nError: ${error.message}`);
                showView(appContainer);
                if (gameList) {
                    gameList.innerHTML = `<div class="error-message"><p>Could not load games.</p><p>Please tap the Refresh button to try again.</p></div>`;
                }
            });
    }

    // --- 5. Event Listeners ---
    if (newGameBtn) newGameBtn.addEventListener('click', () => showView(createGameView));
    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', () => showView(appContainer));
    if (refreshBtn) refreshBtn.addEventListener('click', fetchGames);

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