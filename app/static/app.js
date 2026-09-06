document.addEventListener('DOMContentLoaded', () => {
    let currentSegment = 'overall';
    let currentCategory = 'ALL';
    let currentLimit = 25;
    let allRankedItems = [];

    const statAgents = document.getElementById('stat-agents');
    const statTransactions = document.getElementById('stat-transactions');
    const statAds = document.getElementById('stat-ads');
    const statWhitespace = document.getElementById('stat-whitespace');
    const tbody = document.getElementById('leaderboard-tbody');
    const mopTbody = document.getElementById('mop-tbody');
    const benchmarksTbody = document.getElementById('benchmarks-tbody');
    const adsTbody = document.getElementById('ads-tbody');
    const whitespaceTbody = document.getElementById('whitespace-tbody');
    const paginationInfo = document.getElementById('pagination-info');
    const searchInput = document.getElementById('agent-search-input');
    const limitSelect = document.getElementById('limit-select');
    const categorySelect = document.getElementById('property-category-select');
    const syncBtn = document.getElementById('btn-trigger-sync');
    const syncSpinner = document.getElementById('sync-spinner');
    const syncBtnText = document.getElementById('sync-btn-text');
    const adTriggerBtn = document.getElementById('btn-trigger-ad-analysis');
    const adSpinner = document.getElementById('ad-spinner');
    const adBtnText = document.getElementById('ad-btn-text');
    const modal = document.getElementById('agent-modal');
    const modalClose = document.getElementById('modal-close');

    // 1. Fetch Health Stats
    async function loadHealthStats() {
        try {
            const res = await fetch('/api/v1/health');
            const data = await res.json();

            if (data.status === 'healthy' && data.stats) {
                if (statAgents) statAgents.textContent = Number(data.stats.agents || 0).toLocaleString();
                if (statTransactions) statTransactions.textContent = Number(data.stats.transactions || 0).toLocaleString();
            }

            // Also load ad counts
            const adRes = await fetch('/api/v1/ad-intelligence/campaigns?limit=1');
            if (adRes.ok) {
                const adData = await adRes.json();
                if (statAds) statAds.textContent = Number(adData.active_campaigns_count || 0).toLocaleString();
            }

            const wsRes = await fetch('/api/v1/ad-intelligence/whitespace-opportunities?min_score=70');
            if (wsRes.ok) {
                const wsData = await wsRes.json();
                if (statWhitespace) statWhitespace.textContent = `${wsData.high_roi_count || 0} Pockets`;
            }
        } catch (e) {
            console.error('Error fetching telemetry:', e);
        }
    }

    // 2. Fetch Leaderboard
    async function loadLeaderboard() {
        if (!tbody) return;
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

    // 3. Fetch HDB MOP Clusters
    async function loadMOPClusters() {
        if (!mopTbody) return;
        mopTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-muted">Loading MOP cluster cohorts...</td></tr>`;
        try {
            const res = await fetch('/api/v1/hdb/mop-clusters?limit=50&upgrader_cohort_only=false');
            const data = await res.json();
            const clusters = data.clusters || [];
            if (clusters.length === 0) {
                mopTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-muted">No MOP clusters indexed yet. Trigger Ingestion above!</td></tr>`;
                return;
            }
            mopTbody.innerHTML = clusters.map(c => `
                <tr>
                    <td><strong>${escapeHtml(c.town)}</strong></td>
                    <td>${escapeHtml(c.street_name)} Blk ${escapeHtml(c.block)}</td>
                    <td>${c.lease_commence_year}</td>
                    <td><strong>${c.mop_completion_year}</strong></td>
                    <td><span class="badge badge-reg">${c.estimated_units} Units</span></td>
                    <td>$${c.median_resale_psf} psf</td>
                    <td>
                        <span class="badge ${c.is_mop_upgrader_cohort ? 'badge-rank-1' : 'badge-phase'}">
                            ${c.is_mop_upgrader_cohort ? '🔥 Active Upgrader Cohort' : 'Future Cohort'}
                        </span>
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            mopTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-danger">Failed to load MOP clusters: ${e.message}</td></tr>`;
        }
    }

    // 4. Fetch URA Price Benchmarks
    async function loadMarketBenchmarks() {
        if (!benchmarksTbody) return;
        benchmarksTbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">Loading price benchmarks...</td></tr>`;
        try {
            const res = await fetch('/api/v1/market-benchmarks?limit=50');
            const data = await res.json();
            const benchmarks = data.benchmarks || [];
            if (benchmarks.length === 0) {
                benchmarksTbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">No market benchmarks indexed yet. Trigger Ingestion above!</td></tr>`;
                return;
            }
            benchmarksTbody.innerHTML = benchmarks.map(b => `
                <tr>
                    <td><span class="badge badge-reg">${escapeHtml(b.district)}</span></td>
                    <td><strong>${escapeHtml(b.town)}</strong></td>
                    <td><span class="badge badge-phase">${escapeHtml(b.market_segment)}</span></td>
                    <td>${escapeHtml(b.property_category)}</td>
                    <td><strong style="color: #34D399;">$${b.median_psf.toLocaleString()} psf</strong></td>
                    <td class="text-muted" style="font-size: 0.8rem;">$${b.p25_psf} - $${b.p75_psf} psf</td>
                    <td>$${b.median_quantum.toLocaleString()}</td>
                    <td>${b.quarterly_volume} txs</td>
                </tr>
            `).join('');
        } catch (e) {
            benchmarksTbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-danger">Failed to load benchmarks: ${e.message}</td></tr>`;
        }
    }

    // 5. Fetch Agent 2 Ad Creatives
    async function loadAdCampaigns() {
        if (!adsTbody) return;
        adsTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-muted">Loading active competitor ad campaigns...</td></tr>`;
        try {
            const res = await fetch('/api/v1/ad-intelligence/campaigns?limit=50');
            const data = await res.json();
            const campaigns = data.campaigns || [];
            if (campaigns.length === 0) {
                adsTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-muted">No ads scraped yet. Click "Run Phase 2 Whitespace Analysis" above!</td></tr>`;
                return;
            }
            adsTbody.innerHTML = campaigns.map(ad => `
                <tr>
                    <td><strong>${escapeHtml(ad.page_name)}</strong></td>
                    <td>
                        <div style="font-weight: 600; color: #F3F4F6; margin-bottom: 0.25rem;">${escapeHtml(ad.ad_headline)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(ad.ad_body.substring(0, 120))}...</div>
                    </td>
                    <td>
                        <div class="pill-group">
                            ${(ad.detected_hooks || []).map(h => `<span class="badge badge-reg">${escapeHtml(h)}</span>`).join('')}
                        </div>
                    </td>
                    <td><span class="badge badge-phase">${escapeHtml(ad.target_segment)}</span> (${escapeHtml(ad.target_district)})</td>
                    <td><span class="pill pill-ns">${escapeHtml(ad.cta_type)}</span></td>
                    <td><span class="pill pill-rs">${escapeHtml(ad.media_type)}</span></td>
                    <td><span class="badge badge-rank-1">🟢 Active</span></td>
                </tr>
            `).join('');
        } catch (e) {
            adsTbody.innerHTML = `<tr><td colspan="7" class="text-center py-6 text-danger">Failed to load ads: ${e.message}</td></tr>`;
        }
    }

    // 6. Fetch Agent 3 Whitespace Opportunities
    async function loadWhitespaceOpportunities() {
        if (!whitespaceTbody) return;
        whitespaceTbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">Computing market whitespace scores...</td></tr>`;
        try {
            const res = await fetch('/api/v1/ad-intelligence/whitespace-opportunities?min_score=0&limit=50');
            const data = await res.json();
            const opps = data.opportunities || [];
            if (opps.length === 0) {
                whitespaceTbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-muted">No whitespace opportunities computed yet. Click "Run Phase 2 Whitespace Analysis" above!</td></tr>`;
                return;
            }
            whitespaceTbody.innerHTML = opps.map(opp => {
                let badgeClass = opp.whitespace_score >= 70 ? 'badge-rank-1' : (opp.whitespace_score >= 50 ? 'badge-reg' : 'badge-phase');
                return `
                    <tr>
                        <td>
                            <div style="font-size: 1.25rem; font-weight: 800; color: #EC4899;">${opp.whitespace_score} / 100</div>
                            <span class="badge ${badgeClass}">${opp.whitespace_score >= 70 ? '🔥 High ROI Gap' : 'Moderate'}</span>
                        </td>
                        <td>
                            <strong style="font-size: 1rem; color: #F9FAFB;">${escapeHtml(opp.target_identifier)}</strong>
                            <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(opp.target_type)}</div>
                        </td>
                        <td><span class="badge badge-phase">${escapeHtml(opp.district)}</span> • ${escapeHtml(opp.property_category)}</td>
                        <td style="font-size: 0.85rem; color: #34D399; font-weight: 500;">${escapeHtml(opp.recommended_persona)}</td>
                        <td>
                            <div style="background: rgba(255,255,255,0.03); padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8rem; border-left: 3px solid #EC4899;">
                                ${escapeHtml(opp.recommended_hook_angle)}
                            </div>
                        </td>
                        <td><strong>${opp.estimated_target_units.toLocaleString()}</strong> Units</td>
                    </tr>
                `;
            }).join('');
        } catch (e) {
            whitespaceTbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-danger">Failed to load whitespace: ${e.message}</td></tr>`;
        }
    }

    // Render Leaderboard Table
    function renderTable(items, totalCohort) {
        if (!items || items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-6 text-muted">No agents found for this segment. Trigger ingestion above!</td></tr>`;
            if (paginationInfo) paginationInfo.textContent = `Showing 0 of 0 agents`;
            return;
        }

        if (paginationInfo) paginationInfo.textContent = `Showing ${items.length} of ${totalCohort || items.length} agents (${currentSegment.toUpperCase()})`;

        tbody.innerHTML = items.map(item => {
            let rankBadge = `<span class="badge">${item.rank}</span>`;
            if (item.rank === 1) rankBadge = `<span class="badge badge-rank-1">🥇 #1</span>`;
            else if (item.rank === 2) rankBadge = `<span class="badge badge-rank-2">🥈 #2</span>`;
            else if (item.rank === 3) rankBadge = `<span class="badge badge-rank-3">🥉 #3</span>`;

            return `
                <tr>
                    <td>${rankBadge}</td>
                    <td><div class="agent-name-cell">${escapeHtml(item.agent_name)}</div></td>
                    <td><span class="badge badge-reg">${escapeHtml(item.cea_reg_no)}</span></td>
                    <td><div class="agency-cell">${escapeHtml(item.agency_name)}</div></td>
                    <td><strong>${item.transaction_count}</strong> txs</td>
                    <td>
                        <div class="pill-group">
                            <span class="pill pill-ns">New Sale: ${item.new_sale_count}</span>
                            <span class="pill pill-rs">Resale: ${item.resale_count}</span>
                            <span class="pill pill-rt">Rental: ${item.rental_count}</span>
                        </div>
                    </td>
                    <td><span class="badge ${item.percentile <= 5 ? 'badge-reg' : 'badge-phase'}">Top ${item.percentile}%</span></td>
                    <td style="text-align: right;">
                        <button class="btn btn-outline" style="padding: 0.3rem 0.75rem; font-size: 0.75rem;" onclick="window.viewAgent('${item.cea_reg_no}')">
                            Inspect
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // View Agent Details Modal
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
                </div>
            `;
            modal.classList.add('open');
        } catch (err) {
            alert('Error loading agent: ' + err.message);
        }
    };

    if (modalClose) modalClose.addEventListener('click', () => modal.classList.remove('open'));
    if (modal) modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('open');
    });

    // View Switch Buttons
    document.querySelectorAll('.view-switch-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.view-switch-btn').forEach(b => {
                b.classList.remove('active', 'btn-primary');
                b.classList.add('btn-outline');
            });
            btn.classList.remove('btn-outline');
            btn.classList.add('active', 'btn-primary');

            const targetView = btn.getAttribute('data-view');
            document.querySelectorAll('.view-section').forEach(sec => sec.style.display = 'none');
            
            if (targetView === 'rankings') {
                document.getElementById('view-rankings').style.display = 'block';
                loadLeaderboard();
            } else if (targetView === 'mop') {
                document.getElementById('view-mop').style.display = 'block';
                loadMOPClusters();
            } else if (targetView === 'benchmarks') {
                document.getElementById('view-benchmarks').style.display = 'block';
                loadMarketBenchmarks();
            } else if (targetView === 'ads') {
                document.getElementById('view-ads').style.display = 'block';
                loadAdCampaigns();
            } else if (targetView === 'whitespace') {
                document.getElementById('view-whitespace').style.display = 'block';
                loadWhitespaceOpportunities();
            }
        });
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
    if (searchInput) {
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
    }

    if (limitSelect) {
        limitSelect.addEventListener('change', (e) => {
            currentLimit = parseInt(e.target.value, 10);
            loadLeaderboard();
        });
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            currentCategory = e.target.value;
            loadLeaderboard();
        });
    }

    // Phase 1 Ingestion button
    if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
            syncBtn.disabled = true;
            syncSpinner.style.display = 'inline-block';
            syncBtnText.textContent = 'Ingesting Data...';

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
                    alert(`Phase 1 Ingestion Successful!\n${data.message}\nDuration: ${data.duration_ms}ms`);
                } else {
                    alert(`Ingestion error: ${data.detail || 'Unknown error'}`);
                }
            } catch (err) {
                alert(`Error triggering sync: ${err.message}`);
            } finally {
                syncBtn.disabled = false;
                syncSpinner.style.display = 'none';
                syncBtnText.textContent = 'Phase 1 Ingestion';
            }
        });
    }

    // Phase 2 Ad Analysis button
    if (adTriggerBtn) {
        adTriggerBtn.addEventListener('click', async () => {
            adTriggerBtn.disabled = true;
            adSpinner.style.display = 'inline-block';
            adBtnText.textContent = 'Scraping Ads & Whitespace...';

            try {
                const res = await fetch('/api/v1/ad-intelligence/analyze?sample_agent_limit=25', {
                    method: 'POST',
                });
                const data = await res.json();
                if (res.ok) {
                    await loadHealthStats();
                    await loadAdCampaigns();
                    await loadWhitespaceOpportunities();
                    alert(`Phase 2 Analysis Successful!\n${data.message}\nDuration: ${data.duration_ms}ms`);
                } else {
                    alert(`Ad Analysis error: ${data.detail || 'Unknown error'}`);
                }
            } catch (err) {
                alert(`Error triggering ad analysis: ${err.message}`);
            } finally {
                adTriggerBtn.disabled = false;
                adSpinner.style.display = 'none';
                adBtnText.textContent = 'Run Phase 2 Whitespace Analysis';
            }
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    loadHealthStats();
    loadLeaderboard();
});
