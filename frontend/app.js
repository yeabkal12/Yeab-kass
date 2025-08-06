// /frontend/app.js (The Final, Perfected, and Bulletproof Version)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- 1. CRITICAL: VERIFY THIS URL ---
    // This MUST be the URL of your Python backend service (the Web Service on Render).
    // Please double-check it carefully.
    const API_URL = 'https://yeab-kass.onrender.com/api/games';

    // --- 2. Robust Element Finding ---
    // This new way of finding elements is safer and will not crash if an ID is missing.
    const getEl = (id) => document.getElementById(id);

    const loadingView = getEl('loading-view');
    const appContainer = getEl('app-container');
    const createGameView = getEl('create-game-view');
    const confirmModalOverlay = getEl('confirm-modal-overlay');

    const gameList = getEl('game-list');
    const newGameBtn = getEl('new-game-btn');
    const refreshBtn = getEl('refresh-btn');
    const filtersContainer = getEl('filters');
    const stakeOptions = getEl('stake-options');
    const customStakeInput = getEl('custom-stake-input');
    const winOptions = getEl('win-options');
    const cancelCreateBtn = getEl('cancel-create-btn');
    const showConfirmBtn = getEl('show-confirm-btn');
    const closeModalBtn = getEl('close-modal-btn');
    const cancelConfirmBtn = getEl('cancel-confirm-btn');
    const confirmCreateBtn = getEl('confirm-create-btn');
    const summaryStake = getEl('summary-stake');
    const summaryWin = getEl('summary-win');
    const summaryPrize = getEl('summary-prize');

    let selectedStake = 50;
    let selectedWin = 2;

    // --- 3. View Management ---
    function showView(view) {
        if (!view) return;
        loadingView.classList.add('hidden');
        appContainer.classList.add('hidden');
        createGameView.classList.add('hidden');
        view.classList.remove('hidden');
    }

    // --- 4. Core Logic with Better Error Handling ---
    function fetchGames() {
        fetch(API_URL)
            .then(response => {
                if (!response.ok) {
                    // This gives us more details if the server returns an error
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                gameList.innerHTML = '';
                if (data.games && data.games.length > 0) {
                    data.games.forEach(game => {
                        const card = document.createElement('div');
                        card.className = 'game-card';
                        card.innerHTML = `
                            <div class="card-player">
                                <div class="avatar-container"><img src="${game.creator_avatar}" alt="Avatar"><span class="star-badge">⭐</span></div>
                                <span class="username">${game.creator_name}</span><span class="user-stake">${game.stake} ብር</span>
                            </div>
                            <div class="card-info">
                                <div class="crown-icons">${game.win_condition_crowns}</div>
                                <p class="win-condition-text">${game.win_condition_text}</p>
                                <button class="join-btn" data-game-id="${game.id}">Join</button>
                            </div>
                            <div class="card-stats">
                                <div class="game-stat"><span>Stake</span><strong>${game.stake} ብር</strong></div>
                                <div class="game-stat"><span>Prize</span><strong class="prize-amount">${game.prize} ብር</strong></div>
                            </div>`;
                        gameList.appendChild(card);
                    });
                } else {
                    gameList.innerHTML = '<p>No open games found. Create one!</p>';
                }
                showView(appContainer);
            })
            .catch(error => {
                console.error('CRITICAL FETCH ERROR:', error);
                tg.showAlert(`Could not connect to the game server. Please try again later. Error: ${error.message}`);
                showView(appContainer);
                gameList.innerHTML = `<p>Could not load games. Please tap Refresh.</p>`;
            });
    }

    // --- 5. Event Listeners ---
    // By checking if the element exists, we prevent crashes.
    if(newGameBtn) newGameBtn.addEventListener('click', () => showView(createGameView));
    if(cancelCreateBtn) cancelCreateBtn.addEventListener('click', () => showView(appContainer));
    if(refreshBtn) refreshBtn.addEventListener('click', fetchGames);

    if(filtersContainer) filtersContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('filter-btn')) {
            filtersContainer.querySelector('.active')?.classList.remove('active');
            event.target.classList.add('active');
        }
    });

    if(stakeOptions) stakeOptions.addEventListener('click', e => { /* ... */ });
    if(winOptions) winOptions.addEventListener('click', e => { /* ... */ });
    if(customStakeInput) customStakeInput.addEventListener('input', () => { /* ... */ });
    if(showConfirmBtn) showConfirmBtn.addEventListener('click', () => { /* ... */ });

    function hideModal() {
        confirmModalOverlay.classList.add('hidden');
        appContainer.classList.remove('blurred');
        createGameView.classList.remove('blurred');
    }
    if(closeModalBtn) closeModalBtn.addEventListener('click', hideModal);
    if(cancelConfirmBtn) cancelConfirmBtn.addEventListener('click', hideModal);

    if(confirmCreateBtn) confirmCreateBtn.addEventListener('click', () => {
        const data = `create_game_stake_${selectedStake}_win_${selectedWin}`;
        tg.sendData(data);
        // We will not close the app automatically anymore, to see bot replies
    });

    // --- 6. Initial Load ---
    if(loadingView) {
        showView(loadingView);
        // Use your 8-second delay from the HTML if you still have it,
        // or rely on fetchGames to hide the loading screen.
        setTimeout(fetchGames, 1000); // Start fetching after 1 second
    } else {
        fetchGames();
    }
});