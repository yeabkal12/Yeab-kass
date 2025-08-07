// frontend/app.js (Complete Frontend Code - With Cold Start Handling)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // The API URL is correct.
    const API_URL = 'https://yeab-kass.onrender.com/api/games';

    const getEl = (id) => document.getElementById(id);

    const loadingView = getEl('loading-view');
    const appContainer = getEl('app-container');
    const createGameView = getEl('create-game-view');
    const gameList = getEl('game-list');
    const newGameBtn = getEl('new-game-btn');
    const refreshBtn = getEl('refresh-btn');
    const cancelCreateBtn = getEl('cancel-create-btn');

    function showView(view) {
        if (!view) return;
        if (loadingView) loadingView.classList.add('hidden');
        if (appContainer) appContainer.classList.add('hidden');
        if (createGameView) createGameView.classList.add('hidden');
        view.classList.remove('hidden');
    }

    // --- 4. Core Logic with Client-Side Timeout for Cold Starts ---
    function fetchGames() {
        showView(loadingView);

        // This controller will allow us to cancel the fetch request after a timeout.
        const controller = new AbortController();
        const signal = controller.signal;

        // Set a 15-second timeout.
        const timeoutId = setTimeout(() => {
            controller.abort(); // This will cancel the fetch request.
        }, 15000); // 15 seconds

        fetch(API_URL, { signal }) // Pass the abort signal to the fetch request.
            .then(response => {
                // If we get a response, clear the timeout.
                clearTimeout(timeoutId);
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (!gameList) return;

                gameList.innerHTML = '';
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
                clearTimeout(timeoutId); // Always clear the timeout on error.
                
                // Check if the error was caused by our timeout.
                if (error.name === 'AbortError') {
                    console.error('Fetch timed out (likely a cold start).');
                    tg.showAlert('The server is starting up. This might take a moment. Please try again.');
                    showView(appContainer);
                    if (gameList) {
                        gameList.innerHTML = `<div class="error-message"><p>Server is waking up...</p><p>Please tap Refresh in a few seconds.</p></div>`;
                    }
                } else {
                    // Handle other errors (like network loss).
                    console.error('CRITICAL FETCH ERROR:', error);
                    tg.showAlert(`Could not connect to the game server.\n\nError: ${error.message}`);
                    showView(appContainer);
                    if (gameList) {
                        gameList.innerHTML = `<div class="error-message"><p>Could not load games.</p><p>Please tap the Refresh button to try again.</p></div>`;
                    }
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