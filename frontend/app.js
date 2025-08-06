// /frontend/app.js (Final, Perfected Version with Instant Refresh)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- 1. Get references to ALL views and elements ---
    const loadingView = document.getElementById('loading-view');
    const appContainer = document.getElementById('app-container');
    const createGameView = document.getElementById('create-game-view');
    const confirmModalOverlay = document.getElementById('confirm-modal-overlay');

    const gameList = document.getElementById('game-list');
    const newGameBtn = document.getElementById('new-game-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    const filtersContainer = document.getElementById('filters');
    const stakeOptions = document.getElementById('stake-options');
    const customStakeInput = document.getElementById('custom-stake-input');
    const winOptions = document.getElementById('win-options');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');
    const showConfirmBtn = document.getElementById('show-confirm-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelConfirmBtn = document.getElementById('cancel-confirm-btn');
    const confirmCreateBtn = document.getElementById('confirm-create-btn');
    
    let selectedStake = 50;
    let selectedWin = 2;

    const API_URL = 'https://yeab-game-zone-api.onrender.com/api/games'; // <-- Ensure this is your API URL

    // --- 2. View Management ---
    function showView(view) {
        loadingView.classList.add('hidden');
        appContainer.classList.add('hidden');
        createGameView.classList.add('hidden');
        view.classList.remove('hidden');
    }

    // --- 3. Core Logic ---
    function fetchGames() {
        fetch(API_URL)
            .then(response => response.json())
            .then(data => {
                gameList.innerHTML = '';
                if (data.games && data.games.length > 0) {
                    data.games.forEach(game => {
                        const card = document.createElement('div');
                        card.className = 'game-card';
                        // This is the template for the beautiful game card
                        card.innerHTML = `
                            <div class="card-player">
                                <div class="avatar-container">
                                    <img src="${game.creator_avatar}" alt="Avatar">
                                    <span class="star-badge">⭐</span>
                                </div>
                                <span class="username">${game.creator_name}</span>
                                <span class="user-stake">${game.stake} ብር</span>
                            </div>
                            <div class="card-info">
                                <div class="crown-icons">${game.win_condition_crowns}</div>
                                <p class="win-condition-text">${game.win_condition_text}</p>
                                <button class="join-btn" data-game-id="${game.id}">Join</button>
                            </div>
                            <div class="card-stats">
                                <div class="game-stat">
                                    <span>Stake</span>
                                    <strong>${game.stake} ብር</strong>
                                </div>
                                <div class="game-stat">
                                    <span>Prize</span>
                                    <strong class="prize-amount">${game.prize} ብር</strong>
                                </div>
                            </div>
                        `;
                        gameList.appendChild(card);
                    });
                } else {
                    gameList.innerHTML = '<p>No open games. Create one!</p>';
                }
                showView(appContainer); // Show the main lobby after fetching
            })
            .catch(error => {
                console.error('Error:', error);
                showView(appContainer);
                gameList.innerHTML = '<p>Could not load games. Please Refresh.</p>';
            });
    }

    // --- 4. Event Listeners for the FULL FLOW ---

    newGameBtn.addEventListener('click', () => showView(createGameView));
    cancelCreateBtn.addEventListener('click', () => showView(appContainer));
    refreshBtn.addEventListener('click', fetchGames);
    filtersContainer.addEventListener('click', (event) => { /* ... filter logic ... */ });

    // Handle Clicks on Join Buttons in the Lobby
    gameList.addEventListener('click', event => {
        if (event.target.classList.contains('join-btn')) {
            const gameId = event.target.getAttribute('data-game-id');
            tg.sendData(`join_game_${gameId}`);
            // We no longer close the app here, so the user sees the bot's response
        }
    });

    // Handle the Confirmation Modal
    showConfirmBtn.addEventListener('click', () => { /* ... modal logic ... */ });

    function hideModal() {
        confirmModalOverlay.classList.add('hidden');
        appContainer.classList.remove('blurred');
        createGameView.classList.remove('blurred');
    }
    closeModalBtn.addEventListener('click', hideModal);
    cancelConfirmBtn.addEventListener('click', hideModal);

    // --- THIS IS THE CRITICAL FIX ---
    confirmCreateBtn.addEventListener('click', () => {
        // First, hide the modal and show the main lobby view
        hideModal();
        showView(appContainer);
        gameList.innerHTML = '<p>Creating your game and refreshing the list...</p>';

        // Then, send the data to the bot to create the game in the database
        const data = `create_game_stake_${selectedStake}_win_${selectedWin}`;
        tg.sendData(data);

        // After a short delay, refresh the game list to show the new game
        setTimeout(() => {
            fetchGames();
        }, 1500); // 1.5 second delay to give the server time to process
    });

    // --- 5. Initial Load ---
    showView(loadingView);
    fetchGames();
});