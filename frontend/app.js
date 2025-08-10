// frontend/app.js (Final Version with UI and Logic Injected)

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
    const refreshBtn = getEl('refresh-btn');

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

    // --- Real-Time WebSocket Logic ---
    function connectWebSocket() {
        // Use your actual WebSocket URL
        socket = new WebSocket("wss://yeab-kass.onrender.com/ws");

        socket.onopen = () => {
            console.log("WebSocket connection established.");
            // Optional: Hide any connection error messages
        };

        socket.onclose = () => {
            console.log("WebSocket connection closed.");
            // Optional: Show a connection error message to the user
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            // Optional: Show a connection error message
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list":
                    allGames = data.games;
                    renderGameList(allGames);
                    break;
                case "new_game":
                    // Add to the start of the list so it appears on top
                    allGames.unshift(data.game);
                    renderGameList(allGames);
                    break;
                case "remove_game":
                    allGames = allGames.filter(game => game.id !== data.gameId);
                    removeGameCard(data.gameId);
                    break;
            }
        };
    }

    // =========================================================
    // =========== START: INJECTED UI SECTION ==================
    // =========================================================

    function renderGameList(games) {
        gameListContainer.innerHTML = ''; // Clear previous list
        if (games.length === 0) {
            // Display a more engaging empty state
            gameListContainer.innerHTML = `
                <div class="empty-state">
                    <h3 class="empty-state-title">No Open Games Found</h3>
                    <p style="color: var(--text-muted); margin-bottom: 20px;">Be the first to create one!</p>
                    <button class="empty-state-btn" id="empty-create-btn">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
                        Create New Game
                    </button>
                </div>
            `;
            // Make the button in the empty state also open the modal
            document.getElementById('empty-create-btn').addEventListener('click', showStakeModal);
        } else {
            games.forEach(addGameCard);
        }
    }

    function addGameCard(game) {
        const cardElement = document.createElement('div');
        cardElement.className = 'game-card';
        cardElement.id = `game-${game.id}`;

        const totalPot = game.stake * 2;
        const prize = totalPot - (totalPot * 0.10); // 10% commission

        // This structure matches the modern design
        cardElement.innerHTML = `
            <div class="player-info">
                <div class="avatar"></div> <!-- Placeholder for avatar -->
                <div>
                    <div class="name">${game.creatorName || 'Player***'}</div>
                    <div class="stake">Stake: ${game.stake} ETB</div>
                </div>
            </div>
            <div class="game-details">
                <div class="win-text">👑</div>
                <div class="win-subtext">${game.win_condition} Piece</div>
            </div>
            <div class="stake-details">
                 <div class="prize-label">Prize</div>
                 <div class="prize">${prize.toFixed(2)} ETB</div>
            </div>
            <button class="join-btn">Join</button>
        `;
        gameListContainer.appendChild(cardElement);
    }

    function removeGameCard(gameId) {
        const cardToRemove = getEl(`game-${gameId}`);
        if (cardToRemove) cardToRemove.remove();
        if (gameListContainer.children.length === 0) {
            renderGameList([]);
        }
    }

    // =========================================================
    // =========== END: INJECTED UI SECTION ====================
    // =========================================================

    const showStakeModal = () => {
        mainApp.style.filter = 'blur(5px)';
        stakeModal.classList.remove('hidden');
    };

    const hideStakeModal = () => {
        mainApp.style.filter = 'none';
        stakeModal.classList.add('hidden');
    };

    const updateSummary = () => {
        if (!selectedStake) return;
        const numberOfPlayers = 2;
        const commissionRate = 0.10;
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        const totalPot = selectedStake * numberOfPlayers;
        const finalPrize = totalPot - (totalPot * commissionRate);
        summaryPrizeAmount.textContent = `${finalPrize.toFixed(2)} ETB`;
    };

    const showConfirmModal = () => {
        hideStakeModal();
        mainApp.style.filter = 'blur(5px)';
        confirmModal.classList.remove('hidden');
        updateSummary();
    };

    const hideConfirmModal = () => {
        mainApp.style.filter = 'none';
        confirmModal.classList.add('hidden');
    };

    function setupEventListeners() {
        if (newGameBtn) newGameBtn.addEventListener('click', showStakeModal);

        if (filtersContainer) {
            filtersContainer.addEventListener('click', (event) => {
                const button = event.target.closest('.filter-button');
                if (!button) return;

                filtersContainer.querySelector('.active')?.classList.remove('active');
                button.classList.add('active');

                const filterText = button.textContent.replace('💰 ', '').replace('+', '');
                let filteredGames = allGames;

                if (filterText !== 'All') {
                    if (filterText.includes('-')) {
                        const [min, max] = filterText.split('-').map(Number);
                        filteredGames = allGames.filter(g => g.stake >= min && g.stake <= max);
                    } else {
                        const min = parseInt(filterText);
                        filteredGames = allGames.filter(g => g.stake >= min);
                    }
                }
                renderGameList(filteredGames);
            });
        }

        if (closeStakeModalBtn) closeStakeModalBtn.addEventListener('click', hideStakeModal);
        if (cancelStakeBtn) cancelStakeBtn.addEventListener('click', hideStakeModal);
        if (nextStakeBtn) nextStakeBtn.addEventListener('click', showConfirmModal);

        if (closeConfirmModalBtn) closeConfirmModalBtn.addEventListener('click', hideConfirmModal);
        if (cancelConfirmBtn) cancelConfirmBtn.addEventListener('click', hideConfirmModal);

        if (stakeOptionsGrid) {
            stakeOptionsGrid.addEventListener('click', e => {
                const button = e.target.closest('.option-btn');
                if (button) {
                    stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
                    button.classList.add('selected');
                    selectedStake = parseInt(button.dataset.stake);
                    nextStakeBtn.disabled = false;
                }
            });
        }

        if (winConditionOptions) {
            winConditionOptions.addEventListener('click', e => {
                const button = e.target.closest('.win-option-btn');
                if (button) {
                    winConditionOptions.querySelector('.selected')?.classList.remove('selected');
                    button.classList.add('selected');
                    selectedWinCondition = parseInt(button.dataset.win);
                    createGameBtn.disabled = false;
                }
            });
        }

        // --- Logic to send data via WebSocket ---
        if (createGameBtn) {
            createGameBtn.addEventListener('click', () => {
                if (!selectedStake || !selectedWinCondition || !socket) {
                    console.error("Cannot create game. Stake, win condition, or socket is missing.");
                    return;
                }

                const gameData = {
                    event: "create_game",
                    payload: {
                        stake: selectedStake,
                        winCondition: selectedWinCondition,
                        // You could pass user info from Telegram here
                        // creatorName: tg.initDataUnsafe?.user?.first_name || 'Player'
                    }
                };

                socket.send(JSON.stringify(gameData));
                hideConfirmModal(); // Close the modal after creating the game
            });
        }
    }

    // --- Initial Application Load ---
    const init = () => {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        setupEventListeners();
        connectWebSocket();
    };

    setTimeout(init, 3000); // Simulate loading time
});