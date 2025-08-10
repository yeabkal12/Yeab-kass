// app.js - Final Version

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

    // Stake Modal Elements
    const stakeModal = getEl('stake-modal');
    const closeStakeModalBtn = getEl('close-stake-modal-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const cancelStakeBtn = getEl('cancel-stake-btn');
    const nextStakeBtn = getEl('next-stake-btn');

    // Confirm Modal Elements
    const confirmModal = getEl('confirm-modal');
    const closeConfirmModalBtn = getEl('close-confirm-modal-btn');
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');
    const cancelConfirmBtn = getEl('cancel-confirm-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    // --- WebSocket Logic ---
    function connectWebSocket() {
        socket = new WebSocket("wss://yeab-kass.onrender.com/ws"); // Replace with your WebSocket URL
        socket.onopen = () => console.log("WebSocket connection established.");
        socket.onclose = () => console.log("WebSocket connection closed.");
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.event === "initial_game_list") {
                allGames = data.games;
                renderGameList(allGames);
            } else if (data.event === "new_game") {
                allGames.unshift(data.game); // Add new games to the top
                renderGameList(allGames);
            }
        };
    }

    // --- UI Rendering ---
    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `<h3 class="empty-state-title">No Open Games</h3>`;
        } else {
            games.forEach(addGameCard);
        }
    }

    function addGameCard(game) {
        const cardElement = document.createElement('div');
        cardElement.className = 'game-card';
        cardElement.id = `game-${game.id}`;
        const prize = (game.stake * 2) * 0.9; // 10% commission

        cardElement.innerHTML = `
            <div class="game-card-player">
                <div class="avatar"></div>
            </div>
            <div>
                <div class="username">${game.creatorName || '@Pla***9'}</div>
                <div class="stake">${game.stake} ETB</div>
            </div>
            <div class="game-card-details">
                <div class="icon">👑</div>
                <div class="text">${game.win_condition} Piece</div>
            </div>
            <div class="game-card-actions">
                <div class="prize-label">Prize</div>
                <div class="prize">${prize.toFixed(2)} ETB</div>
                <button class="join-btn">Join</button>
            </div>
        `;
        gameListContainer.appendChild(cardElement);
    }

    // --- Modal Management ---
    const showModal = (modal) => {
        modal.classList.remove('hidden');
        setTimeout(() => { // Allow display change before adding class
            mainApp.style.filter = 'blur(5px)';
            modal.classList.add('active');
        }, 10);
    };

    const hideModal = (modal) => {
        mainApp.style.filter = 'none';
        modal.classList.remove('active');
        setTimeout(() => modal.classList.add('hidden'), 300); // Wait for transition
    };

    // --- Event Listeners ---
    newGameBtn.addEventListener('click', () => showModal(stakeModal));
    closeStakeModalBtn.addEventListener('click', () => hideModal(stakeModal));
    cancelStakeBtn.addEventListener('click', () => hideModal(stakeModal));

    nextStakeBtn.addEventListener('click', () => {
        hideModal(stakeModal);
        updateSummary();
        showModal(confirmModal);
    });

    closeConfirmModalBtn.addEventListener('click', () => hideModal(confirmModal));
    cancelConfirmBtn.addEventListener('click', () => hideModal(confirmModal));

    stakeOptionsGrid.addEventListener('click', e => {
        const button = e.target.closest('.option-btn');
        if (button) {
            stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            selectedStake = parseInt(button.dataset.stake);
            nextStakeBtn.disabled = false;
        }
    });

    winConditionOptions.addEventListener('click', e => {
        const button = e.target.closest('.win-option-btn');
        if (button) {
            winConditionOptions.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            selectedWinCondition = parseInt(button.dataset.win);
            createGameBtn.disabled = false;
        }
    });

    createGameBtn.addEventListener('click', () => {
        if (!socket || !selectedStake || !selectedWinCondition) return;
        const gameData = {
            event: "create_game",
            payload: { stake: selectedStake, winCondition: selectedWinCondition }
        };
        socket.send(JSON.stringify(gameData));
        hideModal(confirmModal);
    });
    
    // --- Summary Logic ---
    function updateSummary() {
        if (!selectedStake) return;
        const prize = (selectedStake * 2) * 0.9;
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        summaryPrizeAmount.textContent = `${prize.toFixed(2)} ETB`;
    }

    // --- Initial Application Load ---
    function init() {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            mainApp.classList.remove('hidden');
            setTimeout(() => loadingScreen.remove(), 500);
            connectWebSocket();
        }, 2000); // Simulate loading time
    }

    init();
});