// frontend/app.js (The Definitive Version with All Logic Combined)

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
    
    // Summary Elements (Crucial for the prize calculation)
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    // --- Real-Time WebSocket Logic ---
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
                    allGames.unshift(data.game); // Add to the beginning of the array
                    addGameCard(data.game, true); // Render it at the top
                    break;
                case "remove_game":
                    allGames = allGames.filter(game => game.id !== data.gameId);
                    removeGameCard(data.gameId);
                    break;
            }
        };
        // ... other socket handlers
    }

    // --- UI Rendering ---

    /**
     * [CORRECTED] Creates a game card with the correct Amharic text.
     */
    const createGameCardElement = (game) => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.id = `game-${game.id}`;
        const maskedUsername = game.creator ? game.creator.substring(0, 4) + '***' + game.creator.slice(-1) : 'Player***';

        card.innerHTML = `
            <div class="card-player-info">
                <div class="player-avatar"><img src="https://i.pravatar.cc/80?u=${game.creator}" alt="Avatar"><span class="star">⭐</span></div>
                <div class="player-name-stake"><span>${maskedUsername}</span><small>${game.stake} ብር</small></div>
            </div>
            <div class="card-game-details">
                <span class="crowns">${'👑'.repeat(game.winCondition)}</span>
                <span>${game.winCondition} ጠጠር</span>
            </div>
            <div class="card-actions">
                <div class="stake-prize-info"><span>Stake: ${game.stake} ብር</span><span class="prize">Prize: ${game.prize} ብር</span></div>
                <button class="join-btn" data-game-id="${game.id}">Join</button>
            </div>
        `;
        card.querySelector('.join-btn').addEventListener('click', () => {
            socket.send(JSON.stringify({ action: "join_game", gameId: game.id }));
        });
        return card;
    };

    const addGameCard = (game, atTop = false) => {
        const emptyState = gameListContainer.querySelector('.empty-state-title');
        if (emptyState) emptyState.remove();
        const cardElement = createGameCardElement(game);
        if (atTop) {
            gameListContainer.prepend(cardElement);
        } else {
            gameListContainer.appendChild(cardElement);
        }
    };

    const removeGameCard = (gameId) => {
        const cardToRemove = getEl(`game-${gameId}`);
        if (cardToRemove) cardToRemove.remove();
        if (gameListContainer.children.length === 0) renderGameList([]);
    };

    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `<h3 class="empty-state-title">No open games. Create one!</h3>`;
        } else {
            games.forEach(game => addGameCard(game, false));
        }
    }

    // --- Modal Logic ---

    /**
     * [CRUCIAL] Calculates and displays the prize based on the selected stake.
     */
    const updateSummary = () => {
        if (!selectedStake) return;
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        const finalPrize = (selectedStake * 2) * 0.90; // The correct calculation
        summaryPrizeAmount.textContent = `${finalPrize.toFixed(2)} ETB`;
    };

    const showConfirmModal = () => {
        hideStakeModal();
        mainApp.style.filter = 'blur(5px)';
        confirmModal.classList.remove('hidden');
        updateSummary(); // This is the crucial call
    };

    const hideConfirmModal = () => { /* ... hides modal and resets state ... */ };
    const showStakeModal = () => { /* ... shows modal ... */ };
    const hideStakeModal = () => { /* ... hides modal ... */ };

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        if (newGameBtn) newGameBtn.addEventListener('click', showStakeModal);
        
        // Filter logic
        if (filtersContainer) {
            filtersContainer.addEventListener('click', (event) => {
                // ... filter logic ...
            });
        }
        
        // Modal buttons
        if (nextStakeBtn) nextStakeBtn.addEventListener('click', showConfirmModal);
        
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
        // ... all other modal close/cancel button listeners
    }

    // --- Initial Application Load ---
    const init = () => {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        setupEventListeners();
        connectWebSocket();
    };
    
    setTimeout(init, 3000);
});