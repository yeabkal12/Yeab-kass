document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    // --- DOM Element References ---
    const getEl = id => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    
    // Stake Modal Elements
    const stakeModal = getEl('stake-modal');
    const closeStakeModalBtn = getEl('close-stake-modal-btn');
    const stakeOptionsGrid = getEl('stake-options-grid');
    const cancelStakeBtn = getEl('cancel-stake-btn');
    const nextStakeBtn = getEl('next-stake-btn');
    
    // Confirm Modal Elements
    const confirmModal = getEl('confirm-modal');
    const closeConfirmModalBtn = getEl('close-confirm-modal-btn');
    const summaryStakeAmount = getEl('summary-stake-amount');
    const winConditionOptions = getEl('win-condition-options');
    const summaryPrizeAmount = getEl('summary-prize-amount');
    const cancelConfirmBtn = getEl('cancel-confirm-btn');
    const createGameBtn = getEl('create-game-btn');

    // --- Application State ---
    let selectedStake = null;
    let selectedWinCondition = null;

    // --- Functions ---
    const showApp = () => {
        loadingScreen.classList.add('hidden');
        mainApp.classList.remove('hidden');
        renderGameList([]); // Initially render an empty list
    };

    const renderGameList = (games) => {
        gameListContainer.innerHTML = '';
        if (games.length === 0) {
            gameListContainer.innerHTML = `
                <h3 class="empty-state-title">Create New Game</h3>
                <button id="empty-state-new-game-btn" class="empty-state-btn">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.41,11.58l-9-9C12.05,2.22,11.55,2,11,2H4C2.9,2,2,2.9,2,4v7c0,0.55,0.22,1.05,0.59,1.42l9,9c0.36,0.36,0.86,0.58,1.41,0.58s1.05-0.22,1.41-0.59l7-7C22.19,13.68,22.19,12.32,21.41,11.58z M12.5,13.5c-0.83,0-1.5-0.67-1.5-1.5s0.67-1.5,1.5-1.5s1.5,0.67,1.5,1.5S13.33,13.5,12.5,13.5z"/></svg>
                    New Game
                </button>`;
            getEl('empty-state-new-game-btn').addEventListener('click', showStakeModal);
        } else {
            // Logic to render actual game cards would go here
        }
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
    
    const showConfirmModal = () => {
        hideStakeModal();
        mainApp.style.filter = 'blur(5px)';
        confirmModal.classList.remove('hidden');
        updateSummary();
    };
    
    const hideConfirmModal = () => {
        mainApp.style.filter = 'none';
        confirmModal.classList.add('hidden');
        // Reset win condition selection
        const currentSelected = winConditionOptions.querySelector('.selected');
        if (currentSelected) currentSelected.classList.remove('selected');
        createGameBtn.disabled = true;
        selectedWinCondition = null;
    };
    
    const updateSummary = () => {
        if (!selectedStake) return;
        const prize = selectedStake * 2 * 0.9; // Assuming 10% commission
        summaryStakeAmount.textContent = `Stake: ${selectedStake} ETB`;
        summaryPrizeAmount.textContent = `${prize.toFixed(2)} ETB`;
    };

    // --- Event Listeners ---
    setTimeout(showApp, 8000); // 8-second loading screen
    newGameBtn.addEventListener('click', showStakeModal);

    // Stake Modal Listeners
    closeStakeModalBtn.addEventListener('click', hideStakeModal);
    cancelStakeBtn.addEventListener('click', hideStakeModal);
    nextStakeBtn.addEventListener('click', showConfirmModal);
    stakeOptionsGrid.addEventListener('click', (e) => {
        const button = e.target.closest('.option-btn');
        if (!button) return;
        
        const currentSelected = stakeOptionsGrid.querySelector('.selected');
        if (currentSelected) currentSelected.classList.remove('selected');
        
        button.classList.add('selected');
        selectedStake = parseInt(button.dataset.stake);
        nextStakeBtn.disabled = false;
    });

    // Confirm Modal Listeners
    closeConfirmModalBtn.addEventListener('click', hideConfirmModal);
    cancelConfirmBtn.addEventListener('click', hideConfirmModal);
    winConditionOptions.addEventListener('click', (e) => {
        const button = e.target.closest('.win-option-btn');
        if (!button) return;
        
        const currentSelected = winConditionOptions.querySelector('.selected');
        if (currentSelected) currentSelected.classList.remove('selected');
        
        button.classList.add('selected');
        selectedWinCondition = parseInt(button.dataset.win);
        createGameBtn.disabled = false; // Enable create button once win condition is set
    });
    
    createGameBtn.addEventListener('click', () => {
        if (selectedStake && selectedWinCondition) {
            tg.showConfirm(`Create game with ${selectedStake} ETB stake and ${selectedWinCondition} piece win condition?`, (ok) => {
                if (ok) {
                    tg.sendData(`create_game:stake_${selectedStake}:win_${selectedWinCondition}`);
                    hideConfirmModal();
                    tg.showAlert('Your game has been created successfully!');
                }
            });
        }
    });
});