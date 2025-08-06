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
    const stakeOptions = document.getElementById('stake-options');
    const customStakeInput = document.getElementById('custom-stake-input');
    const winOptions = document.getElementById('win-options');
    const cancelCreateBtn = document.getElementById('cancel-create-btn');
    const showConfirmBtn = document.getElementById('show-confirm-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelConfirmBtn = document.getElementById('cancel-confirm-btn');
    const confirmCreateBtn = document.getElementById('confirm-create-btn');
    const summaryStake = document.getElementById('summary-stake');
    const summaryWin = document.getElementById('summary-win');
    const summaryPrize = document.getElementById('summary-prize');

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
                    // This is where you would loop through data.games and create game cards
                } else {
                    gameList.innerHTML = '<p>No open games found. Create one!</p>';
                }
                showView(appContainer);
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

    stakeOptions.addEventListener('click', e => {
        if (e.target.classList.contains('option-btn')) {
            stakeOptions.querySelector('.active')?.classList.remove('active');
            e.target.classList.add('active');
            customStakeInput.value = '';
        }
    });
    
    winOptions.addEventListener('click', e => {
        if (e.target.classList.contains('option-btn')) {
            winOptions.querySelector('.active')?.classList.remove('active');
            e.target.classList.add('active');
        }
    });

    customStakeInput.addEventListener('input', () => {
        if (customStakeInput.value) {
            stakeOptions.querySelector('.active')?.classList.remove('active');
        }
    });
    
    showConfirmBtn.addEventListener('click', () => {
        selectedStake = customStakeInput.value || stakeOptions.querySelector('.active')?.getAttribute('data-stake');
        selectedWin = winOptions.querySelector('.active')?.getAttribute('data-win');

        if (!selectedStake || isNaN(selectedStake) || selectedStake <= 0) {
            tg.showAlert('Please select or enter a valid stake.');
            return;
        }
        
        const prizeValue = (parseInt(selectedStake) * 2 * 0.9).toFixed(2);
        summaryStake.textContent = `${selectedStake} ETB`;
        summaryWin.textContent = `${selectedWin} Piece(s)`;
        summaryPrize.textContent = `${prizeValue} ETB`;
        
        appContainer.classList.add('blurred');
        createGameView.classList.add('blurred');
        confirmModalOverlay.classList.remove('hidden');
    });

    function hideModal() {
        confirmModalOverlay.classList.add('hidden');
        appContainer.classList.remove('blurred');
        createGameView.classList.remove('blurred');
    }
    closeModalBtn.addEventListener('click', hideModal);
    cancelConfirmBtn.addEventListener('click', hideModal);

    confirmCreateBtn.addEventListener('click', () => {
        const data = `create_game_stake_${selectedStake}_win_${selectedWin}`;
        tg.sendData(data);
        tg.close();
    });

    // --- 5. Initial Load ---
    showView(loadingView);
    fetchGames();
});