// frontend/app.js (Refactored for Single-Page Views)

document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- View & Element References ---
    const views = document.querySelectorAll('.view');
    const getEl = id => document.getElementById(id);

    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    const filtersContainer = document.querySelector('.filters');

    // Stake View Elements
    const stakeOptionsGrid = getEl('stake-options-grid');
    const nextStakeBtn = getEl('next-stake-btn');

    // Confirm View Elements
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    // --- View Management ---
    function showView(viewId) {
        views.forEach(view => {
            view.classList.add('hidden');
        });
        const targetView = getEl(viewId);
        if (targetView) {
            targetView.classList.remove('hidden');
        }
    }

    // --- Real-Time WebSocket Logic ---
    function connectWebSocket() {
        socket = new WebSocket("wss://yeab-kass.onrender.com/ws");
        socket.onopen = () => console.log("WebSocket connection established.");
        socket.onclose = () => console.log("WebSocket connection closed.");
        socket.onerror = (error) => console.error("WebSocket error:", error);

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list":
                    allGames = data.games;
                    renderGameList(allGames);
                    break;
                case "new_game":
                    allGames.unshift(data.game);
                    renderGameList(allGames);
                    break;
                // ... other cases
            }
        };
    }

    // --- UI Rendering ---
    function renderGameList(games) {
        gameListContainer.innerHTML = ''; // Clear previous list
        if (games.length === 0) {
            // New empty state from the screenshot
            gameListContainer.innerHTML = `
                <div class="empty-state-container">
                    <h2 class="empty-state-title">No Open Games Found</h2>
                    <p class="empty-state-subtitle">Be the first to create one!</p>
                    <div class="create-game-card" id="empty-state-create-btn">
                        <div class="plus-icon">+</div>
                        <div class="create-text">Create New Game</div>
                    </div>
                </div>
            `;
            getEl('empty-state-create-btn').addEventListener('click', () => showView('stake-view'));
        } else {
            games.forEach(addGameCard);
        }
    }

    function addGameCard(game) { /* ... your existing addGameCard logic ... */ }

    // --- Game Creation Flow Logic ---
    function updateSummary() {
        if (!selectedStake) return;
        const numberOfPlayers = 2;
        const commissionRate = 0.10;
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        const totalPot = selectedStake * numberOfPlayers;
        const finalPrize = totalPot - (totalPot * commissionRate);
        summaryPrizeAmount.textContent = `${finalPrize.toFixed(2)} ETB`;
    }

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        // Main header button
        newGameBtn.addEventListener('click', () => showView('stake-view'));

        // Navigation between views
        nextStakeBtn.addEventListener('click', () => {
            updateSummary();
            showView('confirm-view');
        });

        // Universal back/cancel buttons
        document.querySelectorAll('.back-btn, .cancel').forEach(button => {
            button.addEventListener('click', () => {
                const targetViewId = button.getAttribute('data-target');
                showView(targetViewId);
            });
        });

        // Stake selection
        stakeOptionsGrid.addEventListener('click', e => {
            const button = e.target.closest('.option-btn');
            if (button) {
                stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
                button.classList.add('selected');
                selectedStake = parseInt(button.dataset.stake);
                nextStakeBtn.disabled = false;
            }
        });

        // Win condition selection
        winConditionOptions.addEventListener('click', e => {
            const button = e.target.closest('.win-option-btn');
            if (button) {
                winConditionOptions.querySelector('.selected')?.classList.remove('selected');
                button.classList.add('selected');
                selectedWinCondition = parseInt(button.dataset.win);
                createGameBtn.disabled = false;
            }
        });

        // Final "Create Game" action
        createGameBtn.addEventListener('click', () => {
            if (!selectedStake || !selectedWinCondition || !socket) return;
            const gameData = {
                event: "create_game",
                payload: { stake: selectedStake, winCondition: selectedWinCondition }
            };
            socket.send(JSON.stringify(gameData));
            showView('main-view'); // Go back to the main list
        });

        // Filter logic (remains the same)
        filtersContainer.addEventListener('click', (event) => { /* ... your filter logic ... */ });
    }

    // --- Initial Application Load ---
    function init() {
        setupEventListeners();
        connectWebSocket();
        // Show the main view after a delay, hiding the loading view
        setTimeout(() => {
            showView('main-view');
        }, 1500); // Shorter, more realistic loading time
    }

    init();
});