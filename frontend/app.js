// app.js - Final Version with Failsafe Startup and Smart Button

document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- DOM Element References (Defined once at the top for clarity) ---
    const getEl = id => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const statusIndicator = getEl('status-indicator');
    const statusText = getEl('status-text');
    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    const filtersContainer = getEl('filters');
    const stakeModal = getEl('stake-modal');
    const closeStakeModalBtn = getEl('close-stake-modal-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const cancelStakeBtn = getEl('cancel-stake-btn');
    const nextStakeBtn = getEl('next-stake-btn');
    const confirmModal = getEl('confirm-modal');
    const closeConfirmModalBtn = getEl('close-confirm-modal-btn');
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');
    const cancelConfirmBtn = getEl('cancel-confirm-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let socket = null;
    let allGames = [];
    let isConnected = false;

    // --- Central Validation Logic for Create Button ---
    const validateCreateButtonState = () => {
        const selectedStake = stakeOptionsGrid.querySelector('.selected');
        const selectedWinCondition = winConditionOptions.querySelector('.selected');
        
        if (selectedStake && selectedWinCondition && isConnected) {
            createGameBtn.disabled = false;
        } else {
            createGameBtn.disabled = true;
        }
    };

    // --- UI Update Functions ---
    const updateConnectionStatus = (status, text) => {
        statusIndicator.className = status;
        statusText.textContent = text;
    };

    // --- WebSocket Logic ---
    function connectWebSocket() {
        updateConnectionStatus('connecting', 'Connecting...');
        console.log("Attempting to connect to WebSocket...");

        const userId = tg.initDataUnsafe?.user?.id || '12345'; // Fallback for testing
        
        // !!! IMPORTANT: MAKE SURE THIS URL IS CORRECT !!!
        const socketURL = `wss://yeab-game-zone.onrender.com/ws/${userId}`;
        
        socket = new WebSocket(socketURL);

        socket.onopen = () => {
            console.log("SUCCESS: WebSocket connection established.");
            isConnected = true;
            updateConnectionStatus('connected', 'Connected');
            validateCreateButtonState();
        };

        socket.onclose = () => {
            console.warn("WebSocket connection closed.");
            isConnected = false;
            updateConnectionStatus('disconnected', 'Disconnected');
            validateCreateButtonState();
        };
        
        socket.onerror = (error) => {
            console.error("CRITICAL: WebSocket connection failed.", error);
            isConnected = false;
            updateConnectionStatus('disconnected', 'Failed');
            validateCreateButtonState();
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list":
                    allGames = data.games;
                    applyCurrentFilter();
                    break;
                case "new_game":
                    if (!allGames.some(g => g.id === data.game.id)) {
                        allGames.unshift(data.game);
                    }
                    applyCurrentFilter();
                    break;
                case "remove_game":
                    allGames = allGames.filter(g => g.id !== data.gameId);
                    removeGameCard(data.gameId);
                    break;
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

    const getWinConditionText = (condition) => {
        const amharicMap = { 1: "1 ጠጠር ባነገሰ", 2: "2 ጠጠር ባነገሰ", 4: "4 ጠጠር ባነገሰ" };
        return amharicMap[condition] || `${condition} Piece`;
    };

    function addGameCard(game) {
        const cardElement = document.createElement('div');
        cardElement.className = 'game-card';
        cardElement.id = `game-${game.id}`;
        const prize = game.prize.toFixed(2);
        const stake = game.stake.toFixed(2);
        const winText = getWinConditionText(game.win_condition);

        cardElement.innerHTML = `
            <div class="gc-player-info">
                <div class="gc-avatar">🧙</div>
                <div class="gc-name-stake">
                    <span class="gc-name">${game.creatorName || 'Anonymous'}</span>
                    <span class="gc-stake">${stake} ETB</span>
                </div>
            </div>
            <div class="gc-win-condition">
                <span class="gc-icon">💸</span>
                <span class="gc-text">${winText}</span>
            </div>
            <div class="gc-actions">
                <span class="gc-prize-label">Prize</span>
                <span class="gc-prize">${prize} ETB</span>
                <button class="gc-join-btn" data-game-id="${game.id}">Join</button>
            </div>
        `;
        gameListContainer.appendChild(cardElement);
    }

    function removeGameCard(gameId) {
        const cardToRemove = document.getElementById(`game-${gameId}`);
        if (cardToRemove) cardToRemove.remove();
        if (gameListContainer.children.length === 0) {
            gameListContainer.innerHTML = `<h3 class="empty-state-title">No Open Games</h3>`;
        }
    }

    // --- Filter Logic ---
    function applyCurrentFilter() {
        const activeFilterBtn = filtersContainer.querySelector('.filter-button.active');
        if (!activeFilterBtn) return;
        const filter = activeFilterBtn.dataset.filter;
        let filteredGames = [];

        if (filter === 'all') {
            filteredGames = allGames;
        } else if (filter.includes('-')) {
            const [min, max] = filter.split('-').map(Number);
            filteredGames = allGames.filter(g => g.stake >= min && g.stake <= max);
        } else {
            const min = Number(filter);
            filteredGames = allGames.filter(g => g.stake >= min);
        }
        renderGameList(filteredGames);
    }
    
    // --- Event Listeners ---
    function setupEventListeners() {
        filtersContainer.addEventListener('click', (event) => {
            const button = event.target.closest('.filter-button');
            if (!button) return;
            filtersContainer.querySelector('.active')?.classList.remove('active');
            button.classList.add('active');
            applyCurrentFilter();
        });

        // Modals & Game Creation
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
            if (!button) return;
            stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            nextStakeBtn.disabled = false;
        });

        winConditionOptions.addEventListener('click', e => {
            const button = e.target.closest('.win-option-btn');
            if (!button) return;
            winConditionOptions.querySelector('.selected')?.classList.remove('selected');
            button.classList.add('selected');
            validateCreateButtonState(); // Validate when a win condition is chosen
        });

        createGameBtn.addEventListener('click', () => {
            if (createGameBtn.disabled) return; // Prevent clicks if disabled
            
            const selectedStakeEl = stakeOptionsGrid.querySelector('.selected');
            const selectedWinEl = winConditionOptions.querySelector('.selected');

            if (!socket || !selectedStakeEl || !selectedWinEl) return;

            socket.send(JSON.stringify({
                event: "create_game",
                payload: {
                    stake: parseInt(selectedStakeEl.dataset.stake),
                    winCondition: parseInt(selectedWinEl.dataset.win)
                }
            }));
            hideModal(confirmModal);
        });
    }

    const showModal = (modal) => {
        modal.classList.remove('hidden');
        setTimeout(() => { mainApp.style.filter = 'blur(5px)'; modal.classList.add('active'); }, 10);
    };

    const hideModal = (modal) => {
        mainApp.style.filter = 'none';
        modal.classList.remove('active');
        setTimeout(() => modal.classList.add('hidden'), 300);
    };
    
    function updateSummary() {
        const selectedStakeEl = stakeOptionsGrid.querySelector('.selected');
        if (!selectedStakeEl) return;
        const stake = parseInt(selectedStakeEl.dataset.stake);
        const prize = (stake * 2) * 0.9;
        summaryStakeAmount.textContent = `Stake: ${stake} ETB`;
        summaryPrizeAmount.textContent = `${prize.toFixed(2)} ETB`;
    }

    // --- THE FAILSAFE STARTUP SEQUENCE ---
    function init() {
        console.log("Initializing application...");
        
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            mainApp.classList.remove('hidden');
            setTimeout(() => loadingScreen.remove(), 500);
            connectWebSocket();
        }, 1500);

        setupEventListeners();
    }

    // --- Start the Application ---
    init();
});