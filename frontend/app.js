// app.js - Final Version with Development Fallback

document.addEventListener('DOMContentLoaded', () => {
    // --- Initialize Telegram & Basic Setup ---
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    // --- DOM Element References ---
    const getEl = id => document.getElementById(id);
    const loadingScreen = getEl('loading-screen');
    const mainApp = getEl('main-app');
    // ... (all other element references are the same)
    const gameListContainer = getEl('game-list-container');
    const newGameBtn = getEl('new-game-btn');
    const filtersContainer = document.querySelector('.filters');
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
    let selectedStake = null;
    let selectedWinCondition = null;
    let socket = null;
    let allGames = [];

    // --- WebSocket Logic with Robust Error Handling ---
    function connectWebSocket() {
        console.log("Attempting to connect to WebSocket...");

        // =======================================================================
        // --- THIS IS THE FIX ---
        // We now provide a fallback user ID for testing outside of Telegram.
        // The `|| '12345'` acts as our "developer key".
        // =======================================================================
        const userId = tg.initDataUnsafe?.user?.id || '12345'; // Fallback for testing

        // If you are testing and the alert STILL appears, it means you must launch
        // the app from the bot, as Telegram might be blocking the WebApp object.
        if (!tg.initDataUnsafe?.user?.id) {
            console.warn("Telegram user data not found. Using fallback ID for testing.");
        }
        
        console.log("Connecting with User ID:", userId);

        // !!! IMPORTANT: Replace with your actual Render URL !!!
        const socketURL = `wss://yeab-game-zone.onrender.com/ws/${userId}`;
        
        socket = new WebSocket(socketURL);

        socket.onopen = () => {
            console.log("SUCCESS: WebSocket connection established.");
            loadingScreen.style.opacity = '0';
            mainApp.classList.remove('hidden');
            setTimeout(() => loadingScreen.remove(), 500);
        };

        socket.onerror = (error) => {
            console.error("CRITICAL: WebSocket connection failed.", error);
            alert("Connection Error: Unable to connect to the game server. Please check your Render URL and ensure the server is running.");
        };

        // (The rest of the function remains the same)
        socket.onclose = () => { console.warn("WebSocket connection closed."); };
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.event) {
                case "initial_game_list":
                    allGames = data.games;
                    applyCurrentFilter();
                    break;
                case "new_game":
                    if (!allGames.some(g => g.id === data.game.id)) { allGames.unshift(data.game); }
                    applyCurrentFilter();
                    break;
                case "remove_game":
                    allGames = allGames.filter(g => g.id !== data.gameId);
                    removeGameCard(data.gameId);
                    break;
            }
        };
    }
    
    // (The rest of the file is exactly the same as the previous correct version)
    // --- UI Rendering ---
    function renderGameList(games) {
        gameListContainer.innerHTML = '';
        if (games.length === 0) { gameListContainer.innerHTML = `<h3 class="empty-state-title">No Open Games</h3>`; }
        else { games.forEach(addGameCard); }
    }
    const getWinConditionText = (c) => ({1:"1 ጠጠር ባነገሰ",2:"2 ጠጠር ባነገሰ",4:"4 ጠጠር ባነገሰ"}[c]||`${c} Piece`);
    function addGameCard(game) {
        const card=document.createElement('div'); card.className='game-card'; card.id=`game-${game.id}`;
        card.innerHTML=`<div class="gc-player-info"><div class="gc-avatar">🧙</div><div class="gc-name-stake"><span class="gc-name">${game.creatorName||'Anonymous'}</span><span class="gc-stake">${game.stake.toFixed(2)} ETB</span></div></div><div class="gc-win-condition"><span class="gc-icon">💸</span><span class="gc-text">${getWinConditionText(game.win_condition)}</span></div><div class="gc-actions"><span class="gc-prize-label">Prize</span><span class="gc-prize">${game.prize.toFixed(2)} ETB</span><button class="gc-join-btn" data-game-id="${game.id}">Join</button></div>`;
        gameListContainer.appendChild(card);
    }
    function removeGameCard(id){const c=document.getElementById(`game-${id}`);if(c){c.remove();}if(gameListContainer.children.length===0){gameListContainer.innerHTML=`<h3 class="empty-state-title">No Open Games</h3>`;}}
    function applyCurrentFilter(){const btn=filtersContainer.querySelector('.active');const f=btn.dataset.filter;let filtered;if(f==='all'){filtered=allGames;}else if(f.includes('-')){const[min,max]=f.split('-').map(Number);filtered=allGames.filter(g=>g.stake>=min&&g.stake<=max);}else{const min=Number(f);filtered=allGames.filter(g=>g.stake>=min);}renderGameList(filtered);}
    function setupEventListeners(){filtersContainer.addEventListener('click',(e)=>{const b=e.target.closest('.filter-button');if(!b)return;filtersContainer.querySelector('.active')?.classList.remove('active');b.classList.add('active');applyCurrentFilter();});newGameBtn.addEventListener('click',()=>showModal(stakeModal));closeStakeModalBtn.addEventListener('click',()=>hideModal(stakeModal));cancelStakeBtn.addEventListener('click',()=>hideModal(stakeModal));nextStakeBtn.addEventListener('click',()=>{hideModal(stakeModal);updateSummary();showModal(confirmModal);});closeConfirmModalBtn.addEventListener('click',()=>hideModal(confirmModal));cancelConfirmBtn.addEventListener('click',()=>hideModal(confirmModal));stakeOptionsGrid.addEventListener('click',e=>{const b=e.target.closest('.option-btn');if(!b)return;stakeOptionsGrid.querySelector('.selected')?.classList.remove('selected');b.classList.add('selected');selectedStake=parseInt(b.dataset.stake);nextStakeBtn.disabled=false;});winConditionOptions.addEventListener('click',e=>{const b=e.target.closest('.win-option-btn');if(!b)return;winConditionOptions.querySelector('.selected')?.classList.remove('selected');b.classList.add('selected');selectedWinCondition=parseInt(b.dataset.win);createGameBtn.disabled=false;});createGameBtn.addEventListener('click',()=>{if(!socket||!selectedStake||!selectedWinCondition)return;socket.send(JSON.stringify({event:"create_game",payload:{stake:selectedStake,winCondition:selectedWinCondition}}));hideModal(confirmModal);});}
    const showModal=(m)=>{m.classList.remove('hidden');setTimeout(()=>{mainApp.style.filter='blur(5px)';m.classList.add('active');},10);};
    const hideModal=(m)=>{mainApp.style.filter='none';m.classList.remove('active');setTimeout(()=>m.classList.add('hidden'),300);};
    function updateSummary(){if(!selectedStake)return;const p=(selectedStake*2)*0.9;summaryStakeAmount.textContent=`Stake: ${selectedStake} ETB`;summaryPrizeAmount.textContent=`${p.toFixed(2)} ETB`;}
    function init(){console.log("Initializing application...");setupEventListeners();connectWebSocket();}
    init();
});```

### **How to Use This Fix**

1.  **For Real Users (Production):** The app will work perfectly when launched from the Telegram bot. `tg.initDataUnsafe.user.id` will contain their real ID.

2.  **For Your Testing (Development):** You can now open the web app URL directly in your computer or phone browser. The code will see that the Telegram passport is missing and will use the fallback ID `'12345'` to connect to the server, **allowing the app to open successfully for testing.**

After you push this new `app.js`, your problem will be solved.