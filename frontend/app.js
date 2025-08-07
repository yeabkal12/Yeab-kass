// frontend/app.js (This code is already correct)

document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const API_URL = 'https://yeab-kass.onrender.com/api/games';

    const getEl = (id) => document.getElementById(id);

    const loadingView = getEl('loading-view');
    const appContainer = getEl('app-container');
    const createGameView = getEl('create-game-view');
    const gameList = getEl('game-list');
    const newGameBtn = getEl('new-game-btn');
    const refreshBtn = getEl('refresh-btn');
    const cancelCreateBtn = getEl('cancel-create-btn');

    function showView(view) {
        if (!view) return;
        if (loadingView) loadingView.classList.add('hidden');
        if (appContainer) appContainer.classList.add('hidden');
        if (createGameView) createGameView.classList.add('hidden');
        view.classList.remove('hidden');
    }

    function fetchGames() {
        showView(loadingView);
        // ... rest of the fetch logic from the previous step ...
    }

    if (newGameBtn) newGameBtn.addEventListener('click', () => showView(createGameView));
    if (cancelCreateBtn) cancelCreateBtn.addEventListener('click', () => showView(appContainer));
    if (refreshBtn) refreshBtn.addEventListener('click', fetchGames);
    
    fetchGames();
});```

### Action Plan

1.  **Update your `styles.css`** file to include the `.hidden { display: none !important; }` rule.
2.  **Verify your `index.html`** file to ensure the `loading-view`, `app-container`, and `create-game-view` divs are structured as siblings, not nested.
3.  **Redeploy your Static Site** on Render with these updated files.

This will fix the overlapping UI and your application will behave as expected, showing only one view at a time.