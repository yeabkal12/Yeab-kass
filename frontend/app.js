// REPLACE the old renderGameList and addGameCard functions in your app.js with these.

function renderGameList(games) {
    gameListContainer.innerHTML = ''; // Clear previous list
    if (games.length === 0) {
        // Display a more engaging empty state, like in the examples
        gameListContainer.innerHTML = `
            <div class="empty-state">
                <h3 class="empty-state-title">No Open Games Found</h3>
                <p style="color: var(--text-muted); margin-bottom: 20px;">Be the first to create one!</p>
                <button class="empty-state-btn" id="empty-create-btn">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
                    Create New Game
                </button>
            </div>
        `;
        // Make the button in the empty state also open the modal
        document.getElementById('empty-create-btn').addEventListener('click', showStakeModal);
    } else {
        games.forEach(addGameCard);
    }
}

function addGameCard(game) {
    // Remove the empty state if it exists
    const emptyState = gameListContainer.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const cardElement = document.createElement('div');
    cardElement.className = 'game-card';
    cardElement.id = `game-${game.id}`;

    // Calculate prize based on the same 10% commission logic
    const totalPot = game.stake * 2;
    const prize = totalPot - (totalPot * 0.10);

    // This structure matches the new design from the screenshots
    cardElement.innerHTML = `
        <div class="player-info">
            <div class="avatar"></div> <!-- Placeholder for player avatar -->
            <div>
                <div class="name">${game.creatorName || 'Player***'}</div>
                <div class="stake">Stake: ${game.stake} ETB</div>
            </div>
        </div>

        <div class="game-details">
            <div class="win-text">👑</div>
            <div class="win-subtext">${game.win_condition} Piece</div>
        </div>

        <div class="stake-details">
             <div class="prize-label">Prize</div>
             <div class="prize">${prize.toFixed(2)} ETB</div>
        </div>

        <button class="join-btn">Join</button>
    `;

    // You can add an event listener to the join button here if needed
    // cardElement.querySelector('.join-btn').addEventListener('click', () => joinGame(game.id));

    gameListContainer.appendChild(cardElement);
}

// ... the rest of your app.js remains the same ...