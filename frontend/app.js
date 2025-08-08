// frontend/app.js (The Definitive Version with All Logic & Scenarios Implemented)

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
    
    // Modal Elements
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
    let selectedWinCondition = null; // Will store the number (1, 2, or 4)
    let socket = null;
    let allGames = [];

    // --- WebSocket Logic ---
    function connectWebSocket() {
        socket = new WebSocket("wss://yeab-kass.onrender.com/ws");

        socket.onopen = () => console.log("WebSocket connection established.");
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
        // ... other handlers
    }

    // --- UI Rendering ---
    
    /**
     * [FINAL] Creates a game card with the correct dynamic Amharic win condition.
     */
    const createGameCardElement = (game) => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.id = `game-${game.id}`;
        const maskedUsername = game.creator ? game.creator.substring(0, 4) + '***' + game.creator.slice(-1) : 'Player***';
        
        // This dynamically displays the correct Amharic text based on the user's choice
        const winConditionText = `${game.winCondition} ጠጠር ባነገሰ`;

        card.innerHTML = `
            <div class="card-player-info">
                <div class="player-avatar"><img src="https://i.pravatar.cc/80?u=${game.creator}" alt="Avatar"><span class="star">⭐</span></div>
                <div class="player-name-stake"><span>${maskedUsername}</span><small>${game.stake} ብር</small></div>
            </div>
            <div class="card-game-details">
                <span class="crowns">${'👑'.repeat(game.winCondition)}</span>
                <span class="win-condition-text">${winConditionText}</span>
            </div>
            <div class="card-actions">
                <div class="stake-prize-info"><span>Stake: ${game.stake} ብር</span><span class="prize">Prize: ${game.prize} ብር</span></div>
                <button class="join-btn" data-game-id="${game.id}">Join</button>
            </div>`;
        card.querySelector('.join-btn').addEventListener('click', () => {
            socket.send(JSON.stringify({ action: "join_game", gameId: game.id }));
        });
        return card;
    };

    const addGameCard = (game, atTop = false) => {
        const emptyState = gameListContainer.querySelector('.empty-state-container');
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
    
    /**
     * [FINAL] Renders the game list or the correct empty state with the "New Game" button.
     */
    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `
                <div class="empty-state-container">
                    <h3 class="empty-state-title">Create New Game</h3>
                    <button id="empty-state-new-game-btn" class="empty-state-btn">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.41,11.58l-9-9C12.05,2.22,11.55,2,11,2H4C2.9,2,2,2.9,2,4v7c0,0.55,0.22,1.05,0.59,1.42l9,9c0.36,0.36,0.86,0.58,1.41,0.58s1.05-0.22,1.41-0.59l7-7C22.19,13.68,22.19,12.32,21.41,11.58z M12.5,13.5c-0.83,0-1.5-0.67-1.5-1.5s0.67-1.5,1.5-1.5s1.5,0.67,1.5,1.5S13.33,13.5,12.5,13.5z"/></svg>
                        New Game
                    </button>
                </div>`;
            getEl('empty-state-new-game-btn').addEventListener('click', showStakeModal);
        } else {
            games.forEach(game => addGameCard(game, false));
        }
    }

    // --- Modal & Summary Logic ---
    const updateSummary = () => {
        if (!selectedStake) return;
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        const finalPrize = (selectedStake * 2) * 0.90;
        summaryPrizeAmount.textContent = `${finalPrize.toFixed(2)} ETB`;
    };

    const showConfirmModal = () => {
        hideStakeModal();
        mainApp.style.filter = 'blur(5px)';
        confirmModal.classList.remove('hidden');
        updateSummary();
    };
    
    const showStakeModal = () => {
        mainApp.style.filter = 'blur(5px)';
        stakeModal.classList.remove('hidden');
    };
    
    const hideStakeModal = () => {
        mainApp.style.filter = 'none';
        stakeModal.classList.add('hidden');
    };

    const hideConfirmModal = () => {
        mainApp.style.filter = 'none';
        confirmModal.classList.add('hidden');
        // Reset selections for the next game creation
        winConditionOptions.querySelector('.selected')?.classList.remove('selected');
        stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');
        selectedWinCondition = null;
        selectedStake = null;
        createGameBtn.disabled = true;
        nextStakeBtn.disabled = true;
    };

    // --- Event Listener Activation ---
    function setupEventListeners() {
        if (newGameBtn) newGameBtn.addEventListener('click', showStakeModal);

        if (filtersContainer) {
            filtersContainer.addEventListener('click', (event) => {
                const button = event.target.closest('.filter-button');
                if (!button) return;
                filtersContainer.querySelector('.active')?.classList.remove('active');
                button.classList.add('active');
                
                const filterText = button.textContent.replace('💰 ', '').trim();
                let filteredGames;
                if (filterText === 'All') filteredGames = allGames;
                else if (filterText.includes('-')) {
                    const [min, max] = filterText.split('-').map(Number);
                    filteredGames = allGames.filter(g => g.stake >= min && g.stake <= max);
                } else {
                    const min = parseInt(filterText);
                    filteredGames = allGames.filter(g => g.stake >= min);
                }
                renderGameList(filteredGames);
            });
        }
        
        // Stake Modal Listeners
        if (getEl('close-stake-modal-btn')) getEl('close-stake-modal-btn').addEventListener('click', hideStakeModal);
        if (getEl('cancel-stake-btn')) getEl('cancel-stake-btn').addEventListener('click', hideStakeModal);
        if (nextStakeBtn) nextStakeBtn.addEventListener('click', showConfirmModal);
        
        // Confirm Modal Listeners
        if (getEl('close-confirm-modal-btn')) getEl('close-confirm-modal-btn').addEventListener('click', hideConfirmModal);
        if (getEl('cancel-confirm-btn')) getEl('cancel-confirm-btn').addEventListener('click', hideConfirmModal);

        // Selection Listeners
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

        // Final Create Game Button
        if (createGameBtn) {
            createGameBtn.addEventListener('click', () => {
                if (selectedStake && selectedWinCondition && socket?.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        action: "create_game",
                        stake: selectedStake,
                        winCondition: selectedWinCondition
                    }));
                    hideConfirmModal();
                }
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
    
    setTimeout(init, 1000);
});