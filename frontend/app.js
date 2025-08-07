document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    const getEl = id => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const gameListContainer = getEl('game-list-container');
    
    // --- All Modal Element References ---
    // (Stake Modal)
    const stakeModal = getEl('stake-modal');
    const nextStakeBtn = getEl('next-stake-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    // (Confirm Modal)
    const confirmModal = getEl('confirm-modal');
    const winConditionOptions = getEl('win-condition-options');
    const createGameBtn = getEl('create-game-btn');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;

    // =============================================
    // === FEATURE 3: REAL-TIME WEBSOCKET LOGIC ====
    // =============================================
    function connectWebSocket() {
        // Use your backend's WebSocket URL. Use wss:// for deployed apps.
        socket = new WebSocket("ws://localhost:8000/ws");

        socket.onopen = () => {
            console.log("WebSocket connection established.");
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("Received message from server:", data);

            switch (data.event) {
                case "initial_game_list":
                    renderGameList(data.games);
                    break;
                case "new_game":
                    addGameCard(data.game);
                    break;
                case "remove_game":
                    removeGameCard(data.gameId);
                    break;
            }
        };

        socket.onclose = () => {
            console.log("WebSocket connection closed. Attempting to reconnect...");
            setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            socket.close();
        };
    }

    // =============================================
    // ===== FEATURE 1 & 3: LOBBY UI MANAGEMENT ====
    // =============================================
    const createGameCardElement = (game) => {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.id = `game-${game.id}`; // Crucial for removal
        card.innerHTML = `
            <div class="player-info">
                <div class="avatar"></div>
                <span>${game.creator}</span>
            </div>
            <div class="game-details">
                <div class="win-text">${game.winCondition} Piece</div>
                <div class="win-subtext">To Win</div>
            </div>
            <div class="stake-details">
                <div>Stake: ${game.stake}</div>
                <div class="prize">Prize: ${game.prize}</div>
            </div>
            <button class="join-btn" data-game-id="${game.id}">Join</button>
        `;
        // Add event listener for the new "Join" button
        card.querySelector('.join-btn').addEventListener('click', () => {
            socket.send(JSON.stringify({ action: "join_game", gameId: game.id }));
        });
        return card;
    };
    
    const addGameCard = (game) => {
        // Remove empty state message if it exists
        const emptyState = gameListContainer.querySelector('.empty-state-title');
        if (emptyState) emptyState.parentElement.innerHTML = '';

        const cardElement = createGameCardElement(game);
        gameListContainer.appendChild(cardElement);
    };

    const removeGameCard = (gameId) => {
        const cardToRemove = getEl(`game-${gameId}`);
        if (cardToRemove) {
            cardToRemove.remove();
        }
        // If the list is now empty, show the message again
        if (gameListContainer.children.length === 0) {
            renderGameList([]);
        }
    };
    
    const renderGameList = (games) => {
        gameListContainer.innerHTML = ''; // Clean up main lobby
        if (games.length === 0) {
            gameListContainer.innerHTML = `<h3 class="empty-state-title">No open games. Create one!</h3>`;
        } else {
            games.forEach(addGameCard);
        }
    };

    // =============================================
    // ====== FEATURE 2: GAME CREATION LOGIC =======
    // =============================================
    
    // Win Condition Selection Logic
    winConditionOptions.addEventListener('click', (e) => {
        const button = e.target.closest('.win-option-btn');
        if (!button) return;
        
        // Visually highlight the selected button
        winConditionOptions.querySelector('.selected')?.classList.remove('selected');
        button.classList.add('selected');
        
        // Store the selected value
        selectedWinCondition = parseInt(button.dataset.win);
        createGameBtn.disabled = false; // Enable the final create button
    });
    
    // Create Game Button Logic
    createGameBtn.addEventListener('click', () => {
        if (selectedStake && selectedWinCondition && socket.readyState === WebSocket.OPEN) {
            const gameData = {
                action: "create_game",
                stake: selectedStake,
                winCondition: selectedWinCondition
            };
            socket.send(JSON.stringify(gameData));
            hideConfirmModal();
        }
    });

    // --- All other modal logic and event listeners remain the same ---
    const showStakeModal = () => { /* ... */ };
    const hideStakeModal = () => { /* ... */ };
    const showConfirmModal = () => { /* ... */ };
    const hideConfirmModal = () => {
        mainApp.style.filter = 'none';
        confirmModal.classList.add('hidden');
        // Reset selections
        winConditionOptions.querySelector('.selected')?.classList.remove('selected');
        selectedWinCondition = null;
        createGameBtn.disabled = true;
    };
    // ... (rest of the event listeners for opening/closing modals)

    // --- Initial Application Load ---
    const init = () => {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        connectWebSocket(); // Start the real-time connection
    };
    
    setTimeout(init, 3000); // Shorter loading for testing
});