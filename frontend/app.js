document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    // --- DOM Element References ---
    const getEl = id => document.getElementById(id);
    const mainApp = getEl('main-app');
    const loadingScreen = getEl('loading-screen');
    const gameListContainer = getEl('game-list-container');
    const filtersContainer = document.querySelector('.filters'); // Targeting the container
    const newGameBtn = getEl('new-game-btn');
    
    // Modal Elements
    const stakeModal = getEl('stake-modal');
    const confirmModal = getEl('confirm-modal');
    // ... (other modal elements are the same)
    
    // Summary Elements to Update
    const summaryStakeAmount = getEl('summary-stake-amount');
    const summaryPrizeAmount = getEl('summary-prize-amount');
    const createGameBtn = getEl('create-game-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const nextStakeBtn = getEl('next-stake-btn');
    
    // --- Application State ---
    let selectedStake = null;
    let gamesData = [ // MOCK DATA: In a real app, this would be fetched from your server
        { id: 1, username: '@Player1', stake: 50, prize: 90 },
        { id: 2, username: '@Player2', stake: 250, prize: 450 },
        { id: 3, username: '@Player3', stake: 1000, prize: 1800 },
        { id: 4, username: '@Player4', stake: 80, prize: 144 },
        { id: 5, username: '@Player5', stake: 500, prize: 900 },
    ];

    // ================================================================= //
    // ========= SECTION 1: FILTERING LOGIC (NEW IMPLEMENTATION) ========= //
    // ================================================================= //
    
    /**
     * Filters and then renders the game list based on a filter criterion.
     * @param {string} filter - The filter criterion (e.g., "all", "20-100").
     */
    function filterAndRenderGames(filter = "all") {
        let filteredGames = gamesData;

        if (filter !== "all") {
            if (filter.includes('+')) {
                const min = parseInt(filter.replace('+', ''));
                filteredGames = gamesData.filter(game => game.stake >= min);
            } else {
                const [min, max] = filter.split('-').map(Number);
                filteredGames = gamesData.filter(game => game.stake >= min && game.stake <= max);
            }
        }
        
        renderGameList(filteredGames);
    }
    
    // Add a single event listener to the filters container
    filtersContainer.addEventListener('click', (event) => {
        const button = event.target.closest('.filter-button');
        if (!button) return;

        // Update active state visual
        filtersContainer.querySelector('.active')?.classList.remove('active');
        button.classList.add('active');

        // Extract filter value from text content
        let filterValue = "all";
        if (button.textContent !== 'All') {
            filterValue = button.textContent.replace('💰 ', '').replace('+', '');
        }
        
        filterAndRenderGames(filterValue);
    });

    /**
     * Renders the list of games. Now it just renders whatever list it's given.
     * @param {Array} games - The array of game objects to render.
     */
    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `
                <h3 class="empty-state-title">Create New Game</h3>
                <button id="empty-state-new-game-btn" class="empty-state-btn">
                    🎮 New Game
                </button>`;
            getEl('empty-state-new-game-btn').addEventListener('click', showStakeModal);
        } else {
            // Logic to render actual game cards from the 'games' array
            games.forEach(game => {
                const card = document.createElement('div');
                // ... logic to build and append game card ...
                card.textContent = `${game.username} - Stake: ${game.stake}`; // Placeholder
                gameListContainer.appendChild(card);
            });
        }
    }

    // ========================================================================= //
    // ========= SECTION 2: CONFIRMATION MODAL LOGIC (MODIFIED) ================ //
    // ========================================================================= //
    
    /**
     * Shows the confirmation modal and populates it with correct data.
     */
    const showConfirmModal = () => {
        if (!selectedStake) return; // Safety check

        // --- 2.1: Update Stake Display (MODIFIED) ---
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;

        // --- 2.2: Calculate and Display Prize (MODIFIED) ---
        const numberOfPlayers = 2; // Assuming 2 players for now
        const commission = 0.10; // 10%
        const totalPot = selectedStake * numberOfPlayers;
        const totalPrize = totalPot - (totalPot * commission);
        
        summaryPrizeAmount.textContent = `${totalPrize.toFixed(2)} ETB`;
        
        // Show the modal
        hideStakeModal();
        mainApp.style.filter = 'blur(5px)';
        confirmModal.classList.remove('hidden');
    };

    const hideConfirmModal = () => {
        mainApp.style.filter = 'none';
        confirmModal.classList.add('hidden');
    };
    
    const showStakeModal = () => {
        mainApp.style.filter = 'blur(5px)';
        stakeModal.classList.remove('hidden');
    };

    const hideStakeModal = () => {
        mainApp.style.filter = 'none';
        stakeModal.classList.add('hidden');
        // Reset stake selection
        const currentSelected = stakeOptionsGrid.querySelector('.selected');
        if (currentSelected) currentSelected.classList.remove('selected');
        nextStakeBtn.disabled = true;
        selectedStake = null;
    };


    // --- Initial Load & Event Listeners ---
    const init = () => {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        filterAndRenderGames("all"); // Render all games on initial load
    };
    
    setTimeout(init, 3000); // Shortened loading for testing

    newGameBtn.addEventListener('click', showStakeModal);
    
    // Add listeners for modal buttons
    nextStakeBtn.addEventListener('click', showConfirmModal);
    getEl('cancel-stake-btn').addEventListener('click', hideStakeModal);
    getEl('close-stake-modal-btn').addEventListener('click', hideStakeModal);
    
    getEl('cancel-confirm-btn').addEventListener('click', hideConfirmModal);
    getEl('close-confirm-modal-btn').addEventListener('click', hideConfirmModal);

    stakeOptionsGrid.addEventListener('click', (e) => {
        const button = e.target.closest('.option-btn');
        if (!button) return;
        
        const currentSelected = stakeOptionsGrid.querySelector('.selected');
        if (currentSelected) currentSelected.classList.remove('selected');
        
        button.classList.add('selected');
        selectedStake = parseInt(button.dataset.stake);
        nextStakeBtn.disabled = false;
    });

    createGameBtn.addEventListener('click', () => {
        // ... create game logic ...
    });
});