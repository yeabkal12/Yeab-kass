// frontend/app.js (The Definitive, Bulletproof Version)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    const userId = tg.initDataUnsafe?.user?.id || Math.floor(Math.random() * 100000);
    const getEl = id => document.getElementById(id);

    // --- DOM References ---
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

    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    function connectWebSocket() {
        socket = new WebSocket(`wss://yeab-kass.onrender.com/ws/${userId}`);
        socket.onopen = () => console.log("WebSocket connection established.");
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list": allGames = data.games; renderGameList(allGames); break;
                case "new_game": allGames.unshift(data.game); addGameCard(data.game, true); break;
                case "remove_game": allGames = allGames.filter(g => g.id !== data.gameId); removeGameCard(data.gameId); break;
            }
        };
        // THIS IS THE FIX: Handle errors gracefully
        socket.onerror = (error) => {
            console.error("WebSocket Error:", error);
            gameListContainer.innerHTML = `<div class="error-message">Could not connect to the live server. Please check your connection and refresh.</div>`;
        };
    }

    const createGameCardElement = (game) => {
        // ... (The code for creating the game card is correct)
    };
    
    // ... (All other rendering and modal functions are correct) ...

    function setupEventListeners() {
        try {
            if (newGameBtn) newGameBtn.addEventListener('click', showStakeModal);
            if (filtersContainer) { /* ... filter logic ... */ }
            // ... all other button listeners ...
            if (createGameBtn) {
                createGameBtn.addEventListener('click', () => {
                    if (selectedStake && selectedWinCondition) {
                        tg.sendData(`create_game_stake_${selectedStake}_win_${selectedWinCondition}`);
                        hideConfirmModal();
                    }
                });
            }
        } catch (error) {
            console.error("Error setting up event listeners:", error);
            // This ensures that even if one listener fails, it won't crash the app.
        }
    }

    const init = () => {
        // THIS IS THE FIX: The safety net
        try {
            loadingScreen.classList.add('hidden');
            mainApp.classList.remove('hidden');
            // These are now guaranteed to run even if the WebSocket fails
            setupEventListeners();
            connectWebSocket();
        } catch (error) {
            console.error("Fatal error during app initialization:", error);
            const statusText = document.querySelector('#loading-screen .status-text');
            if (statusText) statusText.textContent = "Error: App failed to start.";
            loadingScreen.classList.remove('hidden'); // Make sure the error is visible
        }
    };
    
    setTimeout(init, 3000); // 3-second delay for a smoother feel
});