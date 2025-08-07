document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram Web App ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    // Use the Telegram theme colors for a native feel
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#10101A';

    // --- DOM Element References ---
    const getEl = (id) => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const gameListContainer = getEl('game-list-container');
    const createGameModal = getEl('create-game-modal');
    const newGameButton = getEl('new-game-button');
    const closeModalButton = getEl('close-modal-button');
    const cancelCreateButton = getEl('cancel-create-button');
    const nextCreateButton = getEl('next-create-button');
    const refreshButton = getEl('refresh-button');
    const stakeOptionsContainer = getEl('stake-options');

    // --- State Variables ---
    let selectedStake = null;

    // --- Mock API Data ---
    // In a real app, this would come from your backend.
    const MOCK_GAMES = [
        { id: 1, username: '@Hd1***d', avatar: 'https://i.pravatar.cc/80?u=1', win_condition: 2, stake: 30, prize: 60 },
        { id: 2, username: '@hag***y', avatar: 'https://i.pravatar.cc/80?u=2', win_condition: 2, stake: 500, prize: 1000 },
        { id: 3, username: '@Mzm***5', avatar: 'https://i.pravatar.cc/80?u=3', win_condition: 1, stake: 500, prize: 1000 },
    ];

    // --- Functions ---

    /**
     * Renders the list of game cards or an empty state message.
     * @param {Array} games - An array of game objects.
     */
    function renderGameList(games) {
        gameListContainer.innerHTML = ''; // Clear previous content

        if (!games || games.length === 0) {
            gameListContainer.innerHTML = `
                <div class="empty-state">
                    <p>No open games found. Create one!</p>
                    <button class="create-new-game-btn">🎮 New Game</button>
                </div>
            `;
            // Add event listener to the new button inside the empty state
            gameListContainer.querySelector('.create-new-game-btn').addEventListener('click', showCreateModal);
            return;
        }

        games.forEach(game => {
            const gameCard = document.createElement('div');
            gameCard.className = 'game-card';
            gameCard.innerHTML = `
                <div class="card-left">
                    <div class="player-avatar">
                        <img src="${game.avatar}" alt="Avatar">
                        <span class="star">⭐</span>
                    </div>
                    <span class="player-name">${game.username}</span>
                </div>
                <div class="card-center">
                    <div class="crowns">${'👑'.repeat(game.win_condition)}</div>
                    <div class="win-condition">${game.win_condition} MMC ግጥም</div>
                </div>
                <div class="card-right">
                    <div>
                        <div class="info-label">Stake</div>
                        <div class="info-value">${game.stake} ብር</div>
                    </div>
                    <div>
                        <div class="info-label">Prize</div>
                        <div class="info-value prize">${game.prize} ብር</div>
                    </div>
                </div>
            `;
            const joinButton = document.createElement('button');
            joinButton.className = 'join-button';
            joinButton.textContent = 'Join';
            joinButton.addEventListener('click', () => {
                tg.showConfirm(`Join ${game.username}'s game for ${game.stake} ብር?`, (ok) => {
                    if (ok) {
                        tg.sendData(`join_game_${game.id}`);
                        tg.close();
                    }
                });
            });
            // A more complex layout might need a different structure, this is one way
            const rightSide = gameCard.querySelector('.card-right');
            const newRightContainer = document.createElement('div');
            newRightContainer.style.textAlign = 'right';
            newRightContainer.appendChild(rightSide);
            newRightContainer.appendChild(joinButton);
            gameCard.appendChild(newRightContainer);
            
            gameListContainer.appendChild(gameCard);
        });
    }
    
    /**
     * Fetches game data (currently uses mock data).
     */
    function fetchGames() {
        // In a real app, you would use fetch() here:
        // fetch('YOUR_API_ENDPOINT')
        //   .then(response => response.json())
        //   .then(data => renderGameList(data.games));
        renderGameList(MOCK_GAMES);
    }
    
    /**
     * Shows the main application and hides the loading screen.
     */
    function showApp() {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        fetchGames();
    }

    /**
     * Shows the game creation modal.
     */
    function showCreateModal() {
        createGameModal.classList.remove('hidden');
        mainApp.style.filter = 'blur(5px)';
    }

    /**
     * Hides the game creation modal.
     */
    function hideCreateModal() {
        createGameModal.classList.add('hidden');
        mainApp.style.filter = 'none';
        // Reset selection
        const currentSelected = stakeOptionsContainer.querySelector('.selected');
        if (currentSelected) {
            currentSelected.classList.remove('selected');
        }
        nextCreateButton.disabled = true;
        selectedStake = null;
    }

    // --- Event Listeners ---

    // Show app after the 8-second loading animation
    setTimeout(showApp, 8000);

    // Main interaction buttons
    newGameButton.addEventListener('click', showCreateModal);
    refreshButton.addEventListener('click', fetchGames);
    
    // Modal interaction buttons
    closeModalButton.addEventListener('click', hideCreateModal);
    cancelCreateButton.addEventListener('click', hideCreateModal);
    nextCreateButton.addEventListener('click', () => {
        if (selectedStake) {
            tg.showConfirm(`Create a new game with a stake of ${selectedStake} ብር?`, (ok) => {
                if (ok) {
                    // Send data to your bot
                    tg.sendData(`create_game_stake_${selectedStake}`);
                    hideCreateModal();
                    // Optionally show a success message
                    tg.showAlert('Your game has been created!');
                }
            });
        }
    });

    // Handle stake selection
    stakeOptionsContainer.addEventListener('click', (event) => {
        const button = event.target.closest('.option-button');
        if (!button) return;

        // Remove previous selection
        const currentSelected = stakeOptionsContainer.querySelector('.selected');
        if (currentSelected) {
            currentSelected.classList.remove('selected');
        }

        // Add new selection
        button.classList.add('selected');
        selectedStake = button.dataset.stake;
        nextCreateButton.disabled = false;
    });

});