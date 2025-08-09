// frontend/app.js (The Definitive Version with Robust Connection Handling)

document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    const getEl = id => document.getElementById(id);

    // --- DOM Element References ---
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    const filtersContainer = document.querySelector('.filters');
    const stakeModal = getEl('stake-modal');
    const nextStakeBtn = getEl('next-stake-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const confirmModal = getEl('confirm-modal');
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    // =========================================================
    // =========== START: INJECTED SECTION =====================
    // =========================================================

    /**
     * [INJECTED FIX] Connects to the WebSocket with robust error handling and user feedback.
     */
    function connectWebSocket() {
        // Show a "Connecting..." message in the main lobby area immediately.
        gameListContainer.innerHTML = `<h3 class="empty-state-title">Connecting to server...</h3>`;

        socket = new WebSocket("wss://yeab-kass.onrender.com/ws");

        socket.onopen = () => {
            console.log("WebSocket connection established and ready.");
            // The server will now send the initial game list, which will trigger onmessage.
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list":
                    allGames = data.games;
                    renderGameList(allGames);
                    break;
                case "new_game":
                    allGames.unshift(data.game);
                    addGameCard(data.game, true);
                    break;
                case "remove_game":
                    allGames = allGames.filter(game => game.id !== data.gameId);
                    removeGameCard(data.gameId);
                    break;
            }
        };

        socket.onerror = (error) => {
            console.error("FATAL WebSocket connection error:", error);
            // Display a clear, user-friendly error message in the UI.
            gameListContainer.innerHTML = `
                <div class="error-container">
                    <h3 class="empty-state-title">Connection Error</h3>
                    <p>Could not connect to the game server. Please check your internet connection and try again.</p>
                    <button id="refresh-button-error" class="action-button new-button">Refresh</button>
                </div>
            `;
            // Make the new refresh button work
            getEl('refresh-button-error').addEventListener('click', () => location.reload());
        };
        
        socket.onclose = () => {
            console.warn("WebSocket connection closed.");
            // Optionally, you can inform the user that the connection was lost.
            // This prevents the app from looking frozen if the connection drops during use.
            if (allGames.length > 0) { // Only show if they were already in the lobby
                 tg.showAlert("Connection to the server was lost. Please refresh the page.");
            }
        };
    }

    // =========================================================
    // ============= END: INJECTED SECTION =====================
    // =========================================================

    const createGameCardElement = (game) => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.id = `game-${game.id}`;
        const maskedUsername = game.creator ? `@${game.creator.substring(0, 3)}***${game.creator.slice(-1)}` : '@Player***';
        const avatarUrl = 'assets/avatars/default_avatar.png';

        card.innerHTML = `
            <div class="card-player-info">
                <div class="player-avatar">
                    <img src="${avatarUrl}" alt="Avatar">
                    <span class="star">⭐</span>
                </div>
                <div class="player-details">
                    <span class="player-name">${maskedUsername}</span>
                    <span class="player-stake">${game.stake} ብር</span>
                </div>
            </div>
            <div class="card-game-rules">
                <div class="win-condition">
                    <div class="crowns">${'👑'.repeat(game.winCondition)}</div>
                    <span>${game.winCondition} ጠጠር ባነገሰ</span>
                </div>
                <button class="join-btn" data-game-id="${game.id}">Join</button>
            </div>
            <div class="card-vitals">
                <div class="vital-item">
                    <label>Stake</label>
                    <span>${game.stake} ብር</span>
                </div>
                <div class="vital-item">
                    <label>Prize</label>
                    <span class="prize">${game.prize} ብር</span>
                </div>
            </div>`;
        
        card.querySelector('.join-btn').addEventListener('click', () => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: "join_game", gameId: game.id }));
            }
        });
        return card;
    };

    const addGameCard = (game, atTop = false) => {
        const emptyState = gameListContainer.querySelector('.empty-state-container') || gameListContainer.querySelector('.error-container');
        if (emptyState) emptyState.remove();
        const cardElement = createGameCardElement(game);
        if (atTop) gameListContainer.prepend(cardElement);
        else gameListContainer.appendChild(cardElement);
    };
    
    const removeGameCard = (gameId) => {
        const cardToRemove = getEl(`game-${gameId}`);
        if (cardToRemove) cardToRemove.remove();
        if (gameListContainer.children.length === 0) renderGameList([]);
    };
    
    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `
                <div class="empty-state-container">
                    <h3 class="empty-state-title">Create New Game</h3>
                    <button id="empty-state-new-game-btn" class="empty-state-btn">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.41,11.58l-9-9C12.05,2.22,11.55,2,11,2H4C2.9,2,2,2.9,2,4v7c0,0.55,0.22,1.05,0.59,1.42l9,9c0.36,0.36,0.86,0.58,1.41,0.58s1.05-0.22,1.41-0.59l7-7C22.19,13.68,22.19,12.32,22.19,11.58z M12.5,13.5c-0.83,0-1.5-0.67-1.5-1.5s0.67-1.5,1.5-1.5s1.5,0.67,1.5,1.5S13.33,13.5,12.5,13.5z"/></svg>
                        New Game
                    </button>
                </div>`;
            getEl('empty-state-new-game-btn').addEventListener('click', showStakeModal);
        } else {
            games.forEach(game => addGameCard(game, false));
        }
    }

    const updateSummary = () => { /* ... */ };
    const showConfirmModal = () => { /* ... */ };
    const showStakeModal = () => { /* ... */ };
    const hideStakeModal = () => { /* ... */ };
    const hideConfirmModal = () => { /* ... */ };

    function setupEventListeners() { /* ... */ }

    const init = () => {
        try {
            loadingScreen.classList.add('hidden');
            mainApp.classList.remove('hidden');
            setupEventListeners();
            connectWebSocket();
        } catch (error) {
            // ... error handling
        }
    };
    
    setTimeout(init, 3000);
});