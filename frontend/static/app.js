/**
 * frontend/static/app.js
 * EDITH Shared Client-Side Controller (Alpine.js)
 * Manages asynchronous data fetching, Plotly chart rendering, modal states,
 * and client-side session persistence (sessionStorage) across multi-page navigation.
 */

function edithApp(activePage = 'overview', sessionPersonaId = 'executive') {
  return {
    activePage: activePage,
    personaId: sessionPersonaId || 'executive',
    consoleView: 'briefing',
    
    sourceInfo: {},
    overviewData: {},
    diagnosticData: {},
    workspaceData: {},
    simulationData: {},
    briefingData: {},
    activeDimension: '',
    
    showAuditModal: false,
    accessLogEvents: [],

    showTelemetryModal: false,
    telemetryData: { events: [], rollup: {} },

    showOverrideInput: null,
    overrideReason: '',

    uploadData: null,
    uploading: false,
    configuring: false,
    uploadedFiles: [],
    detectedRelationships: [],
    configForm: {
      dataset_name: '',
      analysis_grain: 'Time Series (Weekly / Monthly / Daily)',
      primary_measure: '',
      primary_measure_label: '',
      primary_measure_unit: '',
      aggregation_type: 'sum',
      distinct_entity_column: '',
      date_column: 'None (Snapshot)',
      dimension_columns: [],
      driver_columns: [],
      identifier_columns: [],
      drop_invalid_rows: true,
      file_roles: null,
      confirmed_relationships: null
    },

    simLevers: {
      price_rollback_pct: 6.0,
      promo_fund_k: 15.0,
      churn_mitigation: true
    },

    chatHistory: [],
    chatQuery: '',
    chatLoading: false,
    aiStatus: {
      is_live: false,
      live_gemini_active: false,
      key_configured: false,
      key_valid: false,
      error_type: null,
      error_message: null,
      badge_text: 'Deterministic Offline Mode',
      provider: 'Deterministic Analytical Engine'
    },
    showApiKeyModal: false,
    apiKeyInput: '',
    savingApiKey: false,

    alertMsg: '',
    alertType: 'success',

    async initPage() {
      // 1. Restore state from sessionStorage (persists across page loads)
      this.restoreSessionState();

      // 2. Fetch active dataset source info and AI status
      await this.loadActiveSource();
      await this.fetchAiStatus();

      // 3. Load page-specific data
      if (this.activePage === 'overview') {
        await this.loadOverview();
      } else if (this.activePage === 'diagnostic') {
        await this.loadDiagnostic();
      } else if (this.activePage === 'workspace') {
        await this.loadWorkspace();
      } else if (this.activePage === 'simulation') {
        await this.loadSimulation();
      } else if (this.activePage === 'console') {
        await this.loadBriefing();
      }
    },

    restoreSessionState() {
      try {
        const savedChat = sessionStorage.getItem('edith_chat_history');
        if (savedChat) {
          this.chatHistory = JSON.parse(savedChat);
        }
        const savedLevers = sessionStorage.getItem('edith_sim_levers');
        if (savedLevers) {
          this.simLevers = JSON.parse(savedLevers);
        }
        const savedDim = sessionStorage.getItem('edith_active_dim');
        if (savedDim) {
          this.activeDimension = savedDim;
        }
      } catch (e) {
        console.warn('Could not restore sessionStorage state:', e);
      }
    },

    saveSessionState() {
      try {
        sessionStorage.setItem('edith_chat_history', JSON.stringify(this.chatHistory));
        sessionStorage.setItem('edith_sim_levers', JSON.stringify(this.simLevers));
        sessionStorage.setItem('edith_active_dim', this.activeDimension);
      } catch (e) {
        console.warn('Could not save sessionStorage state:', e);
      }
    },

    getPersonaName() {
      if (this.personaId === 'general_user') return 'Business User (Plain Language)';
      if (this.personaId === 'regional_lead') return 'Regional Sales Lead (Region B)';
      if (this.personaId === 'analyst') return 'Analyst / RevOps';
      if (this.personaId === 'executive') return 'Executive / CRO';
      return 'Executive / CRO';
    },

    getPersonaBadgeClass() {
      if (this.personaId === 'executive') return 'bg-[#F5E8FF] text-[#6F00B5] border border-[#E9D5FF]';
      if (this.personaId === 'general_user') return 'bg-[#EFF6FF] text-[#1E40AF] border border-[#BFDBFE]';
      if (this.personaId === 'regional_lead') return 'bg-[#FFF8E1] text-[#A15C00] border border-[#FFE082]';
      if (this.personaId === 'analyst') return 'bg-[#EDF7ED] text-[#16803C] border border-[#C8E6C9]';
      return 'bg-[#F5E8FF] text-[#6F00B5] border border-[#E9D5FF]';
    },

    getPersonaBadgeLabel() {
      if (this.personaId === 'executive') return 'Strategic';
      if (this.personaId === 'general_user') return 'Plain Language';
      if (this.personaId === 'regional_lead') return 'Restricted';
      if (this.personaId === 'analyst') return 'Full Access';
      return 'Strategic';
    },

    async openAuditModal() {
      await this.loadAccessLog();
      this.showAuditModal = true;
    },

    async loadAccessLog() {
      try {
        const res = await fetch('/api/access-log?limit=50');
        if (res.ok) {
          const data = await res.json();
          this.accessLogEvents = data.events || [];
        }
      } catch (e) {
        console.error('Failed to load access log:', e);
      }
    },

    async openTelemetryModal() {
      await this.loadTelemetry();
      this.showTelemetryModal = true;
    },

    async loadTelemetry() {
      try {
        const res = await fetch('/api/telemetry?limit=50');
        if (res.ok) {
          this.telemetryData = await res.json();
        }
      } catch (e) {
        console.error('Failed to load telemetry:', e);
      }
    },

    async loadActiveSource() {
      try {
        const res = await fetch('/api/data/source');
        if (res.ok) {
          this.sourceInfo = await res.json();
        }
      } catch (e) {
        console.error('Failed to load active source:', e);
      }
    },

    async switchBenchmark(benchmarkId) {
      try {
        const res = await fetch('/api/data/switch-benchmark', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ benchmark_id: benchmarkId })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to switch benchmark');

        this.sourceInfo = data.source_info || this.sourceInfo;
        this.chatHistory = [];
        this.saveSessionState();
        this.showAlert(data.message, 'success');
        
        // Reload current active screen
        if (this.activePage === 'overview') await this.loadOverview();
        else if (this.activePage === 'diagnostic') await this.loadDiagnostic();
        else if (this.activePage === 'workspace') await this.loadWorkspace();
        else if (this.activePage === 'simulation') await this.loadSimulation();
        else if (this.activePage === 'console') await this.loadBriefing();
      } catch (e) {
        this.showAlert(e.message, 'error');
      }
    },

    async resetToDemo() {
      try {
        const res = await fetch('/api/data/reset-demo', { method: 'POST' });
        if (res.ok) {
          this.showAlert('Successfully reset to built-in B2B SaaS Benchmark.', 'success');
          this.uploadData = null;
          window.location.reload();
        }
      } catch (e) {
        this.showAlert('Failed to reset demo dataset.', 'error');
      }
    },

    async handleFileSelect(event) {
      const files = event.target.files;
      if (files && files.length > 0) await this.uploadFiles(files);
    },

    async handleFileDrop(event) {
      const files = event.dataTransfer.files;
      if (files && files.length > 0) await this.uploadFiles(files);
    },

    async uploadFiles(files) {
      this.uploading = true;
      this.alertMsg = '';
      const formData = new FormData();
      for (const file of files) {
        formData.append('files', file);
      }
      try {
        const res = await fetch('/api/data/upload', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Upload failed');
        
        if (data.files && data.files.length > 1) {
          this.uploadedFiles = data.files.map(f => ({...f, role: 'dimension'}));
          this.detectedRelationships = data.relationships || [];
          // Auto-mark the first file with most numeric columns as fact
          const factFile = this.uploadedFiles.reduce((a, b) => (a.valid_numeric_columns?.length || 0) >= (b.valid_numeric_columns?.length || 0) ? a : b);
          factFile.role = 'fact';
          this.showAlert(`${data.files.length} files profiled. Review relationships below.`, 'success');
        } else {
          // Single file — backward compatible
          this.uploadData = data.files ? data.files[0] : data;
          const file = files[0];
          this.configForm.dataset_name = file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' ').toUpperCase();
          const topKpi = (this.uploadData.kpi_candidates || [])[0]?.column_name;
          this.configForm.primary_measure = topKpi || (this.uploadData.valid_numeric_columns || [])[0] || '';
          this.configForm.primary_measure_label = this.configForm.primary_measure.replace(/_/g, ' ').toUpperCase();
          this.configForm.primary_measure_unit = 'Units';
          this.configForm.date_column = (this.uploadData.valid_date_columns || [])[0] || 'None (Snapshot)';
          this.configForm.analysis_grain = (this.uploadData.valid_date_columns || []).length > 0 ? 'Time Series (Weekly / Monthly / Daily)' : 'Cross-Sectional Snapshot';
          this.configForm.dimension_columns = (this.uploadData.columns || []).filter(c => !(this.uploadData.valid_numeric_columns || []).includes(c) && !(this.uploadData.valid_date_columns || []).includes(c)).slice(0, 4);
          this.configForm.driver_columns = (this.uploadData.valid_numeric_columns || []).filter(c => c !== this.configForm.primary_measure).slice(0, 3);
          this.showAlert(`File profiled (${this.uploadData.total_rows?.toLocaleString()} rows). Review configuration below.`, 'success');
        }
      } catch (e) {
        this.showAlert(e.message, 'error');
      } finally {
        this.uploading = false;
      }
    },

    selectKpiCandidate(colName) {
      if (!colName) return;
      this.configForm.primary_measure = colName;
      this.configForm.primary_measure_label = colName.replace(/_/g, ' ').toUpperCase();
      this.configForm.driver_columns = (this.uploadData?.valid_numeric_columns || []).filter(c => c !== colName).slice(0, 3);
    },

    confirmRelationships() {
      const factFile = this.uploadedFiles.find(f => f.role === 'fact');
      if (!factFile) {
        this.showAlert('Please designate one file as the Primary Fact Table.', 'error');
        return;
      }
      this.uploadData = factFile;
      this.configForm.dataset_name = factFile.filename.replace(/\.[^/.]+$/, '').replace(/_/g, ' ').toUpperCase();
      const topKpi = (factFile.kpi_candidates || [])[0]?.column_name;
      this.configForm.primary_measure = topKpi || (factFile.valid_numeric_columns || [])[0] || '';
      this.configForm.primary_measure_label = this.configForm.primary_measure.replace(/_/g, ' ').toUpperCase();
      this.configForm.primary_measure_unit = 'Units';
      this.configForm.date_column = (factFile.valid_date_columns || [])[0] || 'None (Snapshot)';
      this.configForm.analysis_grain = (factFile.valid_date_columns || []).length > 0 ? 'Time Series (Weekly / Monthly / Daily)' : 'Cross-Sectional Snapshot';
      this.configForm.dimension_columns = (factFile.columns || []).filter(c => !(factFile.valid_numeric_columns || []).includes(c) && !(factFile.valid_date_columns || []).includes(c)).slice(0, 4);
      this.configForm.driver_columns = (factFile.valid_numeric_columns || []).filter(c => c !== this.configForm.primary_measure).slice(0, 3);
      this.configForm.file_roles = this.uploadedFiles.map(f => ({filename: f.filename, role: f.role, join_keys: []}));
      this.configForm.confirmed_relationships = this.detectedRelationships;
    },

    async submitSemanticConfiguration() {
      this.configuring = true;
      try {
        const payload = {
          dataset_name: this.configForm.dataset_name,
          analysis_grain: this.configForm.analysis_grain,
          primary_measure: this.configForm.primary_measure,
          primary_measure_label: this.configForm.primary_measure_label,
          primary_measure_unit: this.configForm.primary_measure_unit,
          aggregation_type: this.configForm.aggregation_type,
          distinct_entity_column: this.configForm.distinct_entity_column,
          date_column: this.configForm.date_column,
          dimension_columns: this.configForm.dimension_columns,
          driver_columns: this.configForm.driver_columns,
          identifier_columns: this.configForm.identifier_columns,
          drop_invalid_rows: this.configForm.drop_invalid_rows,
          file_roles: this.configForm.file_roles,
          confirmed_relationships: this.configForm.confirmed_relationships
        };

        const res = await fetch('/api/data/configure', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Configuration error');

        this.showAlert(data.message, 'success');
        window.location.href = '/overview';
      } catch (e) {
        this.showAlert(e.message, 'error');
      } finally {
        this.configuring = false;
      }
    },

    async loadOverview() {
      try {
        const res = await fetch('/api/overview');
        if (res.ok) {
          this.overviewData = await res.json();
          if (this.overviewData.is_temporal && this.overviewData.time_series?.length > 0) {
            this.$nextTick(() => this.renderOverviewChart());
          }
        }
      } catch (e) {
        console.error('Overview error:', e);
      }
    },

    renderOverviewChart() {
      const elem = document.getElementById('overviewCorridorChart');
      if (!elem || !this.overviewData.time_series) return;

      const ts = this.overviewData.time_series;
      const xVals = ts.map(p => p.week_label || `W${p.week_idx}`);
      const actuals = ts.map(p => p.value);
      const baselines = ts.map(p => p.baseline);
      const lowers = ts.map(p => p.lower_bound);
      const uppers = ts.map(p => p.upper_bound);

      const traces = [
        {
          x: xVals.concat(xVals.slice().reverse()),
          y: uppers.concat(lowers.slice().reverse()),
          type: 'scatter',
          fill: 'toself',
          fillcolor: 'rgba(161, 0, 255, 0.12)',
          line: { color: 'rgba(161, 0, 255, 0.25)', width: 1 },
          hoverinfo: 'skip',
          showlegend: true,
          name: '±2.0σ Expected Corridor'
        },
        {
          x: xVals,
          y: baselines,
          type: 'scatter',
          mode: 'lines',
          line: { color: '#737373', dash: 'dash', width: 1.5 },
          name: 'Baseline Projection'
        },
        {
          x: xVals,
          y: actuals,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#A100FF', width: 2.5 },
          marker: { color: '#6F00B5', size: 6 },
          name: 'Observed Measure'
        }
      ];

      const layout = {
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: { l: 60, r: 20, t: 20, b: 40 },
        font: { family: 'Inter, sans-serif', color: '#555555', size: 11 },
        xaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        yaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        legend: { orientation: 'h', y: 1.15, font: { color: '#555555', size: 11 } }
      };

      Plotly.newPlot(elem, traces, layout, { responsive: true, displayModeBar: false });
    },

    async loadDiagnostic() {
      try {
        const res = await fetch('/api/diagnostic');
        if (res.ok) {
          this.diagnosticData = await res.json();
          const dims = Object.keys(this.diagnosticData.breakdowns || {});
          if (dims.length > 0 && !this.activeDimension) {
            this.activeDimension = dims[0];
          }
          this.$nextTick(() => this.renderDiagnosticCharts());
        }
      } catch (e) {
        console.error('Diagnostic error:', e);
      }
    },

    renderDiagnosticCharts() {
      this.renderDimensionBarChart();
      this.renderDriverCorrelationChart();
    },

    renderDiagnosticDimensionChart() {
      this.renderDimensionBarChart();
    },

    renderDimensionBarChart() {
      const elem = document.getElementById('diagnosticDimChart') || document.getElementById('dimContributionChart');
      if (!elem || !this.diagnosticData.breakdowns || !this.activeDimension) return;

      const rows = this.diagnosticData.breakdowns[this.activeDimension] || [];
      const xLabels = rows.map(r => r[this.activeDimension] || 'Unknown');
      const yValues = rows.map(r => r.curr_value !== null && r.curr_value !== undefined ? r.curr_value : (r.current_value !== null ? r.current_value : 0));
      const unit = this.diagnosticData.primary_measure_unit || '';

      const trace = {
        x: xLabels,
        y: yValues,
        type: 'bar',
        marker: {
          color: '#A100FF',
          line: { color: '#6F00B5', width: 1 }
        },
        hovertemplate: `%{x}: %{y}${unit}<extra></extra>`
      };

      const layout = {
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: { l: 60, r: 20, t: 10, b: 50 },
        font: { family: 'Inter, sans-serif', color: '#555555', size: 11 },
        xaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        yaxis: { 
          color: '#555555', 
          gridcolor: '#EAEAEA', 
          zerolinecolor: '#EAEAEA',
          ticksuffix: unit === '%' ? '%' : ''
        }
      };

      Plotly.newPlot(elem, [trace], layout, { responsive: true, displayModeBar: false });
    },

    renderDriverCorrelationChart() {
      const elem = document.getElementById('driverCorrelationChart');
      if (!elem || !this.diagnosticData.driver_correlations) return;

      const drivers = this.diagnosticData.driver_correlations;
      const xCategories = drivers.map(d => d.label);
      const yValues = drivers.map(d => d.pearson_r);

      const trace = {
        x: xCategories,
        y: yValues,
        type: 'bar',
        marker: {
          color: '#A100FF',
          line: { color: '#6F00B5', width: 1 }
        }
      };

      const layout = {
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: { l: 60, r: 20, t: 10, b: 50 },
        font: { family: 'Inter, sans-serif', color: '#555555', size: 11 },
        xaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        yaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' }
      };

      Plotly.newPlot(elem, [trace], layout, { responsive: true, displayModeBar: false });
    },

    async submitHypothesisFeedback(hypothesisId, action, reason = '') {
      try {
        const res = await fetch('/api/feedback/hypothesis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ hypothesis_id: hypothesisId, action: action, reason: reason })
        });
        if (res.ok) {
          // Mark as submitted in local state
          const finding = (this.workspaceData.findings || []).find(f => f.id === hypothesisId);
          if (finding) finding.feedback_submitted = true;
          this.showAlert(`Feedback recorded: ${action} for ${hypothesisId}`, 'success');
          // Reload workspace to get updated annotations
          await this.loadWorkspace();
        }
      } catch (e) {
        this.showAlert('Failed to submit feedback: ' + e.message, 'error');
      }
    },

    async loadWorkspace() {
      try {
        const res = await fetch('/api/workspace');
        if (res.ok) {
          this.workspaceData = await res.json();
        }
      } catch (e) {
        console.error('Workspace error:', e);
      }
    },

    async loadSimulation() {
      try {
        const res = await fetch('/api/simulation');
        if (res.ok) {
          this.simulationData = await res.json();
          if (this.simulationData.available) {
            this.simLevers = this.simulationData.levers || this.simLevers;
            this.saveSessionState();
            this.$nextTick(() => this.renderSimulationChart());
          }
        }
      } catch (e) {
        console.error('Simulation error:', e);
      }
    },

    async updateSimulationLevers() {
      try {
        this.saveSessionState();
        const res = await fetch('/api/simulation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.simLevers)
        });
        if (res.ok) {
          this.simulationData = await res.json();
          this.renderSimulationChart();
        }
      } catch (e) {
        console.error('Lever update error:', e);
      }
    },

    renderSimulationChart() {
      const elem = document.getElementById('simTrajectoryChart');
      if (!elem || !this.simulationData.trajectory) return;

      const traj = this.simulationData.trajectory;
      const xWeeks = traj.map(t => t.week_label || `W${t.week_idx}`);
      const doNothing = traj.map(t => t.do_nothing_revenue || t.status_quo || 0);
      const simulated = traj.map(t => t.simulated_revenue || t.counterfactual || 0);

      const traces = [
        {
          x: xWeeks,
          y: doNothing,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#737373', dash: 'dash', width: 2 },
          name: 'Status Quo (No Action)'
        },
        {
          x: xWeeks,
          y: simulated,
          type: 'scatter',
          mode: 'lines+markers',
          line: { color: '#A100FF', width: 2.5 },
          marker: { color: '#6F00B5', size: 6 },
          name: 'Simulated Policy Recovery'
        }
      ];

      const layout = {
        paper_bgcolor: '#FFFFFF',
        plot_bgcolor: '#FFFFFF',
        margin: { l: 60, r: 20, t: 20, b: 40 },
        font: { family: 'Inter, sans-serif', color: '#555555', size: 11 },
        xaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        yaxis: { color: '#555555', gridcolor: '#EAEAEA', zerolinecolor: '#EAEAEA' },
        legend: { orientation: 'h', y: 1.15, font: { color: '#555555', size: 11 } }
      };

      Plotly.newPlot(elem, traces, layout, { responsive: true, displayModeBar: false });
    },

    async loadBriefing() {
      try {
        const res = await fetch('/api/briefing');
        if (res.ok) {
          this.briefingData = await res.json();
        }
      } catch (e) {
        console.error('Failed to load briefing:', e);
      }
    },

    get isDemo() {
      if (this.sourceInfo && typeof this.sourceInfo.is_demo === 'boolean') {
        return this.sourceInfo.is_demo;
      }
      return true;
    },

    getWelcomeMessage() {
      if (this.personaId === 'general_user') {
        return "I am active in Business User (Plain Language) mode. Ask me in everyday language about metric trends, which groups had the biggest impact, or what the team is doing next.";
      }
      if (this.personaId === 'regional_lead') {
        return "I am active in Regional Sales Lead (Region B) mode. Ask me about regional performance, authorized field actions, and localized customer trends.";
      }
      if (this.personaId === 'analyst') {
        return "I am active in Analyst / RevOps mode. Ask me about econometric decompositions, Difference-in-Differences proofs, and causal lineage.";
      }
      return "I am active in Executive / CRO mode. Ask me about high-level incident scale, verified root causes, and strategic decision trade-offs.";
    },

    getStarterQuestions() {
      if (!this.isDemo) {
        if (this.personaId === 'general_user') {
          return [
            'What factors affect this metric?',
            'Which category has the highest concentration?',
            'What are the key takeaways from this data?',
            'Are there any unusual outliers in this file?'
          ];
        }
        if (this.personaId === 'analyst') {
          return [
            'Show the numeric driver correlations',
            'Break down variance across all dimensions',
            'Display IQR and distribution quantiles',
            'Summarize data quality and null percentages'
          ];
        }
        return [
          'What factors affect the active metric?',
          'Which segments show the greatest concentration?',
          'Which drivers have the strongest correlation?',
          'What operational actions are recommended?'
        ];
      }
      if (this.personaId === 'general_user') {
        return [
          'Why did sales drop?',
          'What happened in Region B?',
          'What is the recovery plan?',
          'Why did we rule out warehouse issues?'
        ];
      }
      if (this.personaId === 'regional_lead') {
        return [
          'What caused the Region B revenue deficit?',
          'What field actions are authorized for my role?',
          'Explain the pricing elasticity in Region B',
          'What is the status of the VIP accounts?'
        ];
      }
      if (this.personaId === 'analyst') {
        return [
          'Show the full mathematical decomposition',
          'Explain the Difference-in-Differences proof',
          'Compare H1 pricing vs H2 competitor campaign',
          'Why is H8 supply constraint refuted?'
        ];
      }
      return [
        'What is the primary root cause?',
        'What decision should we approve first?',
        'Explain the volume vs price impact',
        'What is the 8-week projected recovery?'
      ];
    },

    sendStarterQuery(query) {
      this.chatQuery = query;
      this.submitChat();
    },

    async submitChat() {
      const q = this.chatQuery.trim();
      if (!q || this.chatLoading) return;

      this.chatHistory.push({ role: 'user', content: q });
      this.chatQuery = '';
      this.chatLoading = true;
      this.saveSessionState();
      this.scrollToBottom();

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: q,
            chat_history: this.chatHistory,
            simulation_levers: this.simLevers
          })
        });

        let data;
        const resText = await res.text();
        try {
          data = JSON.parse(resText);
        } catch (jsonErr) {
          throw new Error(resText || `HTTP ${res.status}`);
        }

        if (!res.ok) throw new Error(data.detail || data.message || 'Failed to get answer');

        this.chatHistory.push({
          role: 'assistant',
          content: data.answer,
          metadata: data.metadata || null
        });
        this.saveSessionState();
      } catch (e) {
        this.chatHistory.push({
          role: 'assistant',
          content: `Error: ${e.message}`,
          metadata: { error_type: 'network', error_message: e.message }
        });
        this.saveSessionState();
      } finally {
        this.chatLoading = false;
        this.scrollToBottom();
      }
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const box = document.getElementById('chatStreamBox');
        if (box) box.scrollTop = box.scrollHeight;
      });
    },

    showAlert(msg, type = 'success') {
      this.alertMsg = msg;
      this.alertType = type;
    },

    formatNumber(val, unit = '') {
      if (val === null || val === undefined || isNaN(val)) return '0.0';
      const num = Number(val);
      if (unit === '$') {
        return `$${Math.abs(num).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}`;
      }
      if (unit === '%') {
        return `${num.toFixed(1)}%`;
      }
      return `${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })} ${unit}`.trim();
    },

    formatTime(isoStr) {
      if (!isoStr) return '';
      try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      } catch (e) {
        return isoStr;
      }
    },

    async fetchAiStatus() {
      try {
        const res = await fetch('/api/ai/status');
        if (res.ok) {
          this.aiStatus = await res.json();
        }
      } catch (e) {
        console.error('Failed to fetch AI status:', e);
      }
    },

    resetChat() {
      this.chatHistory = [];
      this.chatQuery = '';
      this.saveSessionState();
      this.showAlert('Chat conversation reset.', 'success');
    },

    async saveApiKey(isReset = false) {
      this.savingApiKey = true;
      const keyToSend = isReset ? '' : this.apiKeyInput.trim();
      try {
        const res = await fetch('/api/ai/key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: keyToSend })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to verify key');

        this.showApiKeyModal = false;
        this.apiKeyInput = '';
        await this.fetchAiStatus();
        this.showAlert(data.message, 'success');
      } catch (e) {
        this.showAlert(e.message, 'error');
      } finally {
        this.savingApiKey = false;
      }
    },

    formatInlineMarkdown(text) {
      if (!text) return '';
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="bg-[#F0F0F0] px-1 py-0.5 rounded text-[11px] font-mono text-[#6F00B5]">$1</code>');
    },

    formatMarkdown(text) {
      if (!text) return '';
      
      const tables = [];
      const tableRegex = /(?:^|\n)(\|(?:[^\n]+\|)+\s*\n\|(?:\s*:?-+:?\s*\|)+\s*(?:\n\|(?:[^\n]+\|)+)+)/g;
      
      let processed = text.replace(tableRegex, (match) => {
        const lines = match.trim().split('\n').map(l => l.trim()).filter(l => l.length > 0);
        if (lines.length < 3) return match;
        
        const headerCells = lines[0].split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        const bodyLines = lines.slice(2);
        
        let html = '<div class="overflow-x-auto my-2"><table class="w-full text-xs text-left border border-[#E5E5E5] rounded bg-white shadow-2xs">';
        html += '<thead class="bg-[#FAFAFA] text-[#171717] font-semibold border-b border-[#E5E5E5]"><tr>';
        headerCells.forEach(cell => {
          html += `<th class="p-2 border-r border-[#E5E5E5] last:border-r-0">${this.formatInlineMarkdown(cell)}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        bodyLines.forEach(row => {
          const cells = row.split('|').map(c => c.trim()).filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
          html += '<tr class="border-b border-[#F0F0F0] last:border-b-0 hover:bg-[#FAFAFA]">';
          cells.forEach(cell => {
            html += `<td class="p-2 border-r border-[#E5E5E5] last:border-r-0">${this.formatInlineMarkdown(cell)}</td>`;
          });
          html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        const placeholder = `@@@TABLE_${tables.length}@@@`;
        tables.push(html);
        return '\n' + placeholder + '\n';
      });

      let formatted = processed
        .replace(/### (.*?)\n/g, '<h4 class="font-bold text-xs text-[#171717] mt-2 mb-1">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="bg-[#F0F0F0] px-1 py-0.5 rounded text-[11px] font-mono text-[#6F00B5]">$1</code>')
        .replace(/^- (.*)/gm, '<li class="ml-4 list-disc text-xs text-[#555555]">$1</li>')
        .replace(/^\d+\. (.*)/gm, '<li class="ml-4 list-decimal text-xs text-[#555555]">$1</li>')
        .replace(/\n/g, '<br/>');

      tables.forEach((tbl, idx) => {
        formatted = formatted.replace(`@@@TABLE_${idx}@@@`, tbl);
      });

      return formatted;
    }
  };
}
