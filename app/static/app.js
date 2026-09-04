document.addEventListener('DOMContentLoaded', () => {
    let currentSegment = 'overall';
    let currentCategory = 'ALL';
    let currentLimit = 25;
    let allRankedItems = [];

    const statAgents = document.getElementById('stat-agents');
    const statAgencies = document.getElementById('stat-agencies');
    const statTransactions = document.getElementById('stat-transactions');
    const statLatency = document.getElementById('stat-latency');
    const tbody = document.getElementById('leaderboard-tbody');
    const paginationInfo = document.getElementById('pagination-info');
    const searchInput = document.getElementById('agent-search-input');
    const limitSelect = document.getElementById('limit-select');
    const categorySelect = document.getElementById('property-category-select');
    const syncBtn = document.getElementById('btn-trigger-sync');
    const syncSpinner = document.getElementById('sync-spinner');
    const syncBtnText = document.getElementById('sync-btn-text');
    const modal = document.getElementById('agent-modal');
    const modalClose = document.getElementById('modal-close');

    // 1. Fetch Health Stats
    async function loadHealthStats() {
        const start = performance.now();
        try {
            const res = await fetch('/api/v1/health');
            const data = await res.json();
            const elapsed = Math.round(performance.now() - start);

            if (data.status === 'healthy' && data.stats) {
                statAgents.textContent = Number(data.stats.agents).toLocaleString();
                statAgencies.textContent = Number(data.stats.agencies).toLocaleString();
                statTransactions.textContent = Number(data.stats.transactions).toLocaleString();
                statLatency.textContent = `Latency: ${elapsed}ms • Snapshots: ${data.stats.rank_snapshots}`;
            }
        } catch (e) {
            console.error('Error fetching health:', e);
        }
    }

    // 2. Fetch Leaderboard
    async function loadLeaderboard() {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">Loading leaderboard records...</td></tr>`;
        try {
            const res = await fetch(`/api/v1/agent-rankings?segment=${currentSegment}&property_category=${currentCategory}&limit=${currentLimit}`);
            const data = await res.json();
            allRankedItems = data.items || [];
            renderTable(allRankedItems, data.total_cohort_size);
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-danger">Failed to load rankings: ${e.message}</td></tr>`;
        }
    }

    // 3. Render Table
    function renderTable(items, totalCohort) {
        if (!items || items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">No agents found for this segment. Trigger ingestion above!</td></tr>`;
            paginationInfo.textContent = `Showing 0 of 0 agents`;
            return;
        }

        paginationInfo.textContent = `Showing ${items.length} of ${totalCohort || items.length} agents (${currentSegment.toUpperCase()})`;

        tbody.innerHTML = items.map(item => {
            let rankBadge = `<span class="badge">${item.rank}</span>`;
            if (item.rank === 1) rankBadge = `<span class="badge badge-rank-1">🥇 #1</span>`;
            else if (item.rank === 2) rankBadge = `<span class="badge badge-rank-2">🥈 #2</span>`;
            else if (item.rank === 3) rankBadge = `<span class="badge badge-rank-3">🥉 #3</span>`;

            return `
                <tr>
                    <td>${rankBadge}</td>
                    <td>
                        <div class="agent-name-cell">${escapeHtml(item.agent_name)}</div>
                    </td>
                    <td><span class="badge badge-reg">${escapeHtml(item.cea_reg_no)}</span></td>
                    <td>
                        <div class="agency-cell">${escapeHtml(item.agency_name)}</div>
                    </td>
                    <td><strong>${item.transaction_count}</strong> txs</td>
                    <td>
                        <div class="pill-group">
                            <span class="pill pill-ns">New Sale: ${item.new_sale_count}</span>
                            <span class="pill pill-rs">Resale: ${item.resale_count}</span>
                            <span class="pill pill-rt">Rental: ${item.rental_count}</span>
                        </div>
                    </td>
                    <td>
                        <span class="badge ${item.percentile <= 5 ? 'badge-reg' : 'badge-phase'}">
                            Top ${item.percentile}%
                        </span>
                    </td>
                    <td style="text-align: right;">
                        <button class="btn btn-outline" style="padding: 0.3rem 0.75rem; font-size: 0.75rem;" onclick="window.viewAgent('${item.cea_reg_no}')">
                            Inspect
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // 4. View Agent Details Modal
    window.viewAgent = async function(ceaRegNo) {
        try {
            const res = await fetch(`/api/v1/agents/${ceaRegNo}`);
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Agent not found');

            document.getElementById('modal-agent-name').textContent = data.agent_name;
            document.getElementById('modal-agent-reg').textContent = data.cea_reg_no;

            const modalBody = document.getElementById('modal-agent-body');
            modalBody.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 1.25rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; background: rgba(0,0,0,0.25); padding: 1rem; border-radius: 8px;">
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.75rem;">AGENCY</div>
                            <div style="font-weight: 600; font-size: 0.9rem;">${escapeHtml(data.agency.agency_name)}</div>
                            <div style="color: var(--text-muted); font-size: 0.75rem;">Licence: ${data.agency.licence_no}</div>
                        </div>
                        <div>
                            <div style="color: var(--text-muted); font-size: 0.75rem;">STATUS / CONTACT</div>
                            <div style="font-weight: 600; color: #34D399; font-size: 0.9rem;">${data.status}</div>
                            <div style="color: var(--text-muted); font-size: 0.75rem;">${data.contact_number || 'N/A'}</div>
                        </div>
                    </div>

                    <div>
                        <h4 style="font-size: 0.85rem; margin-bottom: 0.5rem; text-transform: uppercase; color: var(--text-muted);">Trailing 12-Month Performance</h4>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem;">
                            <div style="background: rgba(255,255,255,0.04); padding: 0.75rem; border-radius: 6px; text-align: center;">
                                <div style="font-size: 0.7rem; color: var(--text-muted);">Overall Rank</div>
                                <div style="font-size: 1.25rem; font-weight: 700;">#${data.rankings.overall?.rank || '-'}</div>
                                <div style="font-size: 0.7rem; color: #34D399;">${data.rankings.overall?.transactions_count || 0} txs</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.04); padding: 0.75rem; border-radius: 6px; text-align: center;">
                                <div style="font-size: 0.7rem; color: var(--text-muted);">New Sale Rank</div>
                                <div style="font-size: 1.25rem; font-weight: 700;">#${data.rankings.new_sale?.rank || '-'}</div>
                                <div style="font-size: 0.7rem; color: #60A5FA;">${data.rankings.new_sale?.transactions_count || 0} txs</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.04); padding: 0.75rem; border-radius: 6px; text-align: center;">
                                <div style="font-size: 0.7rem; color: var(--text-muted);">Resale Rank</div>
                                <div style="font-size: 1.25rem; font-weight: 700;">#${data.rankings.resale?.rank || '-'}</div>
                                <div style="font-size: 0.7rem; color: #34D399;">${data.rankings.resale?.transactions_count || 0} txs</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.04); padding: 0.75rem; border-radius: 6px; text-align: center;">
                                <div style="font-size: 0.7rem; color: var(--text-muted);">Rental Rank</div>
                                <div style="font-size: 1.25rem; font-weight: 700;">#${data.rankings.rental?.rank || '-'}</div>
                                <div style="font-size: 0.7rem; color: #FBBF24;">${data.rankings.rental?.transactions_count || 0} txs</div>
                            </div>
                        </div>
                    </div>

                    <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
                        Total Historical Lifetime Records: <strong>${data.total_historical_transactions}</strong>
                    </div>
                </div>
            `;
            modal.classList.add('open');
        } catch (err) {
            alert('Error loading agent: ' + err.message);
        }
    };

    // Close modal
    modalClose.addEventListener('click', () => modal.classList.remove('open'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('open');
    });

    // Segment Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSegment = btn.getAttribute('data-segment');
            loadLeaderboard();
        });
    });

    // Search filter
    searchInput.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase().trim();
        if (!q) {
            renderTable(allRankedItems);
            return;
        }
        const filtered = allRankedItems.filter(item => 
            item.cea_reg_no.toLowerCase().includes(q) || 
            item.agent_name.toLowerCase().includes(q) ||
            item.agency_name.toLowerCase().includes(q)
        );
        renderTable(filtered);
    });

    // Limit selector
    limitSelect.addEventListener('change', (e) => {
        currentLimit = parseInt(e.target.value, 10);
        loadLeaderboard();
    });

    // Category selector
    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            currentCategory = e.target.value;
            loadLeaderboard();
        });
    }

    // Sync pipeline button
    syncBtn.addEventListener('click', async () => {
        syncBtn.disabled = true;
        syncSpinner.style.display = 'inline-block';
        syncBtnText.textContent = 'Ingesting & Computing...';

        try {
            const res = await fetch('/api/v1/ingest/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sample_size: 150, use_fixtures: false })
            });
            const data = await res.json();
            if (res.ok) {
                await loadHealthStats();
                await loadLeaderboard();
                alert(`Ingestion Successful!\n${data.message}\nDuration: ${data.duration_ms}ms`);
            } else {
                alert(`Ingestion error: ${data.detail || 'Unknown error'}`);
            }
        } catch (err) {
            alert(`Error triggering sync: ${err.message}`);
        } finally {
            syncBtn.disabled = false;
            syncSpinner.style.display = 'none';
            syncBtnText.textContent = 'Run Ingestion Pipeline';
        }
    });

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Initial load
    loadHealthStats();
    loadLeaderboard();
});
