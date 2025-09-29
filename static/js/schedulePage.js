const app = Vue.createApp({
    data() {
        return {
            managedGames: [], // managed games filtered from allGames (already sorted)
            allGames: [], // All fetched games from the backend (already sorted)
            filteredGames: [], // Games to display in the table (filtered by team)
            expandedGameId: null, // ID of the currently expanded game card
            managedTeams: [], // Managed teams
            followedTeams: [], // Followed teams
            selectedTeams: [], // Teams selected for inclusion in the table
            isLoading: true, // Show a loading indicator while fetching games
            showReasonPopup: false, // Controls popup visibility
            popupReason: "", // Stores the reason to display in the popup
            selectedGame: null, // To store the game details for the modal
            showPlayedGames: false, // Controls whether played games are shown 
            showUpdateJopoxModal: false, // Päivitä Jopox -modalin näkyvyys
            form: {
                league_selected: '',
                league_options: [],
                event_selected: '',
                event_options: [],
                SiteNameLabel: '',
                HomeTeamTextbox: '',
                guest_team: '',
                AwayCheckbox: false,
                game_location: '',
                game_date: '',
                game_start_time: '',
                game_duration: '',
                game_public_info: '',
                game_groups: [],
                selected_game_group_ids: [],
                deadline_date: '',
                deadline_time: ''
            },
            updatedFields: {}, // Will hold the fields that have been updated
            hasJopox: false,
            toast: {
                show: false,
                type: 'success',   // 'success' | 'warning' | 'error'
                message: ''
              },
            toastTimer: null,
            isBulkCreating: false,
            icons: {
                check: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
                warn:  `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 9v4m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
                error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 8v5m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>`,
                info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 9v4m0 3h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
              }



        };
    },
    methods: {
        fetchGamesAndCompare() {
            this.isLoading = true;
          
            Promise.all([
                fetch('/api/schedules').then(response => response.json()),
                this.hasJopox
                ? fetch('/api/jopox_games').then(r => r.json())
                : Promise.resolve([]) // ei aktivoitu → ei haeta
            ])
            .then(([tulospalveluData, jopoxGames]) => {
                // Save Tulospalvelu.fi data for rendering game cards
                if (tulospalveluData && Array.isArray(tulospalveluData.managed_games)) {
                    console.log('Tulospalvelu data:', tulospalveluData);
                    console.log('Jopox data:', jopoxGames);

                    const tulospalveluGames = tulospalveluData.managed_games;  // Käytetään oikeaa kenttää
                    // Filter out duplicate Game IDs
                    const uniqueGames = [];
                    const seenGameIDs = new Set();
                    for (const game of tulospalveluGames) {
                        if (!seenGameIDs.has(game['Game ID'])) {
                            seenGameIDs.add(game['Game ID']);
                            uniqueGames.push(game);
                        }
                    }
                    this.allGames = uniqueGames;
                    this.managedGames = uniqueGames.filter(game => game.Type === 'manage');
            
                } else {
                    console.error('Unexpected Tulospalvelu response:', tulospalveluData);
                }

            // Send data to backend for comparison if jopoxGames is not empty

            if (this.hasJopox) {
                return fetch('/api/compare', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tulospalvelu_games: this.managedGames, // Only unique and managed games sent for comparison
                        jopox_games: jopoxGames, // Assuming Jopox data is in `.data`
                    }),
                })
                .then(response => response.json())
                .then(comparisonResults => {
                    // Update game cards with comparison results
                    this.managedGames = this.managedGames.map(game => {
                        const match = comparisonResults.find(
                            result => result.game['Game ID'] === game['Game ID']
                        );
                        return {
                            ...game,
                            match_status: match?.match_status || 'red', // Default to red if no match
                            reason: match?.reason || 'No match found',
                            best_match: match?.best_match || null, // Include best_match details if available
                            uid: match?.best_match?.uid || null, // Include unique UID for later use
                            warning: match?.warning || null, // Include warning if available
                        };
                        
                    });
                    this.allGames = this.allGames.map(game => {
                        const managedGame = this.managedGames.find(
                            managed => managed['Game ID'] === game['Game ID']
                        );
                        if (managedGame) {
                            // Jos peli löytyy managedGames-listasta, käytä päivitettyjä tietoja
                            return { ...game, ...managedGame };
                        }
                        return game; // Muuten pidä alkuperäinen
                    });

                    this.filterGames();
                });

            } else {
            this.filterGames();
            return;
              
            }
            })
            .catch(error => {
                console.error('Error during fetching or comparison:', error);
            })
            .finally(() => {
                this.isLoading = false;
            });
        },

        fetchTeams() {
            fetch('/api/teams')
                .then(response => response.json())
                .then(data => {
                    this.managedTeams = data.managed_teams; // Includes 'team_id'
                    this.followedTeams = data.followed_teams; // Includes 'team_id'
                    // Default selection uses 'team_id'
                    this.selectedTeams = data.managed_teams.map(team => team.team_id);
                    this.filterGames(); // Immediately filter games based on managed teams
                })
                .catch(error => {
                    console.error('Error fetching teams:', error);
                });
        },
        

        toggleTeam(team_id) {
            if (this.selectedTeams.includes(team_id)) {
                this.selectedTeams = this.selectedTeams.filter(id => id !== team_id);
            } else {
                this.selectedTeams.push(team_id);
            }
            this.filterGames(); // Update the table with new selection
        },

        togglePlayedGames() {
            this.showPlayedGames = !this.showPlayedGames;
            this.filterGames(); // Reapply filtering
        },
        
        async bulkCreateJopox() {
            if (this.isBulkCreating) return;
            this.isBulkCreating = true;
            try {
                this.isLoading = true;
                // Eligible: managed (not followed-only), not in past, red status
                const eligible = this.filteredGames.filter(g => {
                    const managed = this.managedTeams.some(t => t.team_id === g['Team ID']);
                    const notPast = !this.isPastDay(g.SortableDate);
                    const isRed = (g.match_status === 'red');
                    return managed && notPast && isRed;
                });

                if (eligible.length === 0) {
                    this.showToast('Ei lisättäviä otteluita.', 'info', 2500);
                    return;
                }

                const payload = {
                    items: eligible.map(game => ({
                        game
                    }))
                };
                console.log('Bulk create payload:', payload);

                const resp = await fetch('/api/create_jopox', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const res = await resp.json().catch(() => ({}));
                console.log('Bulk create response:', res);

                const itemsArr = Array.isArray(res?.items) ? res.items : [];
                const okCount = itemsArr.filter(i => i.status === 'ok').length;
                const failCount = itemsArr.length > 0 ? (itemsArr.length - okCount) : 0;

                if (failCount === 0 && okCount > 0) {
                    this.showToast(`Lisätty Jopoxiin ${okCount} ottelua.`, 'success', 4000);
                } else if (failCount > 0) {
                    this.showToast('Osa lisäyksistä vaati tarkennusta tai epäonnistui.', 'warning', 7000);
                    console.log('create_jopox response (bulk):', res);
                } else {
                    this.showToast('Palvelin ei palauttanut odotettua vastausta.', 'error', 4000);
                }
            } catch (e) {
                console.error('Bulk create error', e);
                this.showToast('Bulk-lisäys epäonnistui.', 'error', 4000);
            } finally {
                this.isBulkCreating = false;
                this.fetchGamesAndCompare();
            }
        },
        
        filterGames() {
            if (!this.allGames || this.allGames.length === 0) {
                this.filteredGames = [];
                return;
            }
        
            if (this.selectedTeams.length === 0) {
                this.filteredGames = [];
                return;
            }
        
            // Filter games based on selected teams
            let filtered = this.allGames.filter(game =>
                this.selectedTeams.includes(String(game['Team ID']))
            );
        
            // Further filter out played games if `showPlayedGames` is false
            if (!this.showPlayedGames) {
                filtered = filtered.filter(game => {
                    try {
                        const gameDateTime = new Date(game.SortableDate); // Use SortableDate for comparison
                        const now = new Date();
        
                        // Compare only the day (ignore time)
                        const gameDateWithoutTime = new Date(
                            gameDateTime.getFullYear(),
                            gameDateTime.getMonth(),
                            gameDateTime.getDate()
                        );
                        const nowWithoutTime = new Date(
                            now.getFullYear(),
                            now.getMonth(),
                            now.getDate()
                        );
        
                        return gameDateWithoutTime >= nowWithoutTime; // Include only current and future games
                    } catch (error) {
                        console.error('Error filtering game by date:', game, error);
                        return false; // Exclude games with invalid dates
                    }
                });
            }
        
            this.filteredGames = filtered;
        },
        
        toggleGameDetails(gameId) {
            this.expandedGameId = this.expandedGameId === gameId ? null : gameId;
        },    
        
        showReason(reason) {
            if (reason) {
                alert(reason); // Display the reason for yellow or red status
            }
        },
    
        getButtonColor(teamName) {
            const colorMap = {
                musta: '#282828', // Light Gray
                punainen: '#ff5151', // Light Red
                sininen: '#2c778f', // Light Blue
                keltainen: '#f0f095', // Light Yellow
                valkoinen: '#cccccc', // Light White
                vihreä: '#137f13', // Light Green
            };
        
            const lowerCaseName = teamName.toLowerCase();
            for (const [key, value] of Object.entries(colorMap)) {
                if (lowerCaseName.includes(key)) {
                    return value; // Return the color if found
                }
            }
            return '#E0E0E0'; // Default light gray
        },
        
        getTextColor(backgroundColor, isSelected) {
            // Explicit override for very dark colors like black
            if (backgroundColor === '#282828') {
                return isSelected ? 'white' : '#E0E0E0'; // White text when selected, light gray when unselected
            }
        
            // Calculate contrast for other colors
            const color = backgroundColor.replace('#', '');
            const r = parseInt(color.substring(0, 2), 16);
            const g = parseInt(color.substring(2, 4), 16);
            const b = parseInt(color.substring(4, 6), 16);
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        
            // If unselected, always use darker text for visibility
            if (!isSelected) {
                return brightness > 155 ? 'black' : '#444444'; // Use slightly darker gray for better contrast
            }
        
            // Return white for dark backgrounds and black for light backgrounds when selected
            return brightness > 155 ? 'black' : 'white';
        },
        getRowStyle(game) {
            // Check if the game belongs to a managed team
            const isManaged = this.managedTeams.some(team => team.team_id === game['Team ID']);
            const isFollowed = this.followedTeams.some(team => team.team_id === game['Team ID']);
            
            const isBetweenManagedTeams =
                this.managedTeams.some(team => team.team_id === game['Home Team ID']) &&
                this.managedTeams.some(team => team.team_id === game['Away Team ID']);

            if (isBetweenManagedTeams) {
                return {
                    backgroundColor: '#ffffcc', // Highlight color for games between managed teams
                    color: '#000000',
                };
            }

            if (isManaged) {
                // Use the team-specific color for managed teams
                const backgroundColor = this.getButtonColor(game['Team Name']);
                const textColor = this.getTextColor(backgroundColor, true); // Adjust text color for contrast
                return {
                    backgroundColor: backgroundColor,
                    color: textColor,
                };
            } else if (isFollowed) {
                // Default color for followed teams
                return {
                    backgroundColor: '#ffffff', // Default light gray for followed teams
                    color: '#000000', // Black text for better contrast
                };
            }
        
            // Default styles if no match
            return {
                backgroundColor: 'transparent',
                color: '#000000',
            };
        },

        getDayName(sortableDate) {
            if (!sortableDate || typeof sortableDate !== 'string') {
                return 'Invalid Day';
            }
        
            // Map English day abbreviations to Finnish
            const dayMap = {
                Sat: 'La', // Saturday
                Sun: 'Su', // Sunday
                Mon: 'Ma', // Monday
                Tue: 'Ti', // Tuesday
                Wed: 'Ke', // Wednesday
                Thu: 'To', // Thursday
                Fri: 'Pe', // Friday
            };
        
            // Extract the day abbreviation (first three characters)
            const englishDay = sortableDate.split(',')[0];
            return dayMap[englishDay] || 'Invalid Day'; // Use the map or return a fallback
        },

        isPastDay(sortableDate) {
            try {
                const date = new Date(sortableDate); // Parse SortableDate
                const now = new Date();
        
                // Compare days only
                const dateWithoutTime = new Date(
                    date.getFullYear(),
                    date.getMonth(),
                    date.getDate()
                );
                const nowWithoutTime = new Date(
                    now.getFullYear(),
                    now.getMonth(),
                    now.getDate()
                );
                
                return dateWithoutTime < nowWithoutTime;
            } catch (error) {
                console.error('Error parsing SortableDate:', sortableDate, error);
                return false; // Default to "not past" in case of an error
            }
        },
                          
                
        isTeamSelected(teamName) {
            // Check if a team is selected
            return this.selectedTeams.includes(teamName);
        },

        isNotManagedTeam(game) {
            return !this.managedTeams.some(team => team.team_id === game['Team ID']);
        },

        toggleReason(game) {
            if (game.reason) {
                this.popupReason = game.reason.replace(/\. /g, '<br>'); // Format the reason
                this.showReasonPopup = true; // Show modal
            }
        },
        
        showModal(event, reason) {
            if (!reason) {
                console.error("No reason provided for modal");
                return;
            }
            this.popupReason = reason;
        
            this.$nextTick(() => {
                const modal = document.querySelector(".modal-window");
        
                if (!modal) {
                    console.error("Modal element not found");
                    return;
                }

                if (this.showReasonPopup && this.popupReason === reason) {
                    this.closeModal();
                    return;
                }
            
        
                // Hanki kursorin sijainti
                const cursorX = event.clientX;
                const cursorY = event.clientY;
        
                // Näytä modal-ikkuna tilapäisesti mittojen laskemista varten
                modal.style.visibility = "hidden";
                modal.style.display = "block";
        
                const modalWidth = modal.offsetWidth;
                const modalHeight = modal.offsetHeight;
        
                // Lasketaan modalin sijainti
                const scrollX = window.scrollX || window.pageXOffset;
                const scrollY = window.scrollY || window.pageYOffset;
        
                const arrowOffsetX = 0.05 * modalWidth; // Nuolen 5% offset modalin oikeasta reunasta
                const arrowOffsetY = 0.2 * modalHeight; // Nuolen 10% offset modalin alareunasta
                const topPosition = cursorY + scrollY + arrowOffsetY + 8 ; // Modalin alareuna siirtyy ylöspäin
                const leftPosition = cursorX + scrollX - (modalWidth - arrowOffsetX); // Modalin sijainti suhteessa nuoleen
                
                modal.style.position = "absolute";
                modal.style.top = `${topPosition}px`;
                modal.style.left = `${leftPosition}px`;
        
                // Näytä modal
                modal.style.visibility = "visible";
                modal.style.display = "block";
                this.showReasonPopup = true;
        
            });
        },
        
        toggleModal(event, reason) {
            // Jos modal on jo auki ja syy on sama, sulje modal
            if (this.showReasonPopup && this.popupReason === reason) {
                this.closeModal();
            } else {
                // Muuten avaa modal uudelleen
                this.showModal(event, reason);
            }
        },             
                
       

        closeModal() {
            this.showReasonPopup = false; // Hide the modal
            this.popupReason = ''; // Clear the reason text
        },
        
        openUpdateModal(game) {
            this.selectedGame = game; // Tallenna valittu peli
        
            // Lähetä backendiin pyyntö hakea olemassa olevat jopox-tiedot best matchin uid:llä
            const uid = game.best_match.uid;
            console.log('haetaan tietoja uid:llä:', uid);
            fetch(`/api/jopox_form_information?uid=${uid}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {

                this.form.league_selected = data.league_selected || null;
                this.form.league_options = data.league_options || [];

                // Tarkistetaan onko league_selected jo mukana listassa arvon perusteella
                if (
                    this.form.league_selected &&
                    !this.form.league_options.some(opt => opt.value === this.form.league_selected.value)
                ) {
                    this.form.league_options.push(this.form.league_selected);
                }

                this.form.event_selected = data.event_selected || null;
                this.form.event_options = data.event_options || [];

                // Sama logiikka eventille (valinnainen riippuen käytöstä)
                if (
                    this.form.event_selected &&
                    !this.form.event_options.some(opt => opt.value === this.form.event_selected.value)
                ) {
                    this.form.event_options.push(this.form.event_selected);
                }

                this.form.SiteNameLabel = data.SiteNameLabel || '';
                this.form.HomeTeamTextbox = data.HomeTeamTextbox || '';
                this.form.guest_team = data.guest_team || '';
                this.form.AwayCheckbox = data.AwayCheckbox || false;
                this.form.game_location = data.game_location || '';
                this.form.game_date = data.game_date || '';
                this.form.game_start_time = data.game_start_time || '';
                this.form.game_duration = data.game_duration || '';
                this.form.game_public_info = data.game_public_info || '';
                const gameGroups = data.game_groups || data.game_group_list || [];
                this.form.game_groups = gameGroups;
                this.form.selected_game_group_ids = gameGroups
                    .filter(group => group && group.checked)
                    .map(group => group.id);
                this.form.deadline_date = data.GameDeadLineTextBox || '';
                this.form.deadline_time = data.GameDeadLineTimeTextBox || '';

                console.log('Fetched Jopox data:', data);
                this.showUpdateJopoxModal = true; // Näytä Päivitä Jopox -modal
                this.compareUpdates(game, data);
                
                this.$nextTick(() => {
                    const contentDiv = document.getElementById("public_info");
                    if (contentDiv) {
                        contentDiv.innerHTML = this.form.game_public_info; // Asetetaan HTML-muodossa
                    }
                })
            })

             // Käytetään nextTick asettamaan sisältö oikein contenteditable-kenttään
            

            .catch(error => {
                console.error('Error fetching Jopox data:', error);
            });


        },
    
        compareUpdates(game, data) {
            console.log('compareUpdates called with:', game, data);
            const tp = game || {};
            const jx = data || {};
            this.updatedFields = {};
            const changes = [];

            // helpers
            const clean = s => (s ?? '').toString()
                .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                .replace(/\s+/g, ' ').trim().toLowerCase();

            const mark = (key, label, oldVal, newVal) => {
                const oldV = oldVal ?? '';
                const newV = newVal ?? '';
                if (oldV !== newV) {
                this.updatedFields[key] = true;
                changes.push(`${label}: '${oldV || '—'}' → '${newV || '—'}'`);
                }
                this.form[key] = newV;
            };

            const suggestAlias = (sideFullName, baseTeamName) => {
                const fTok = clean(sideFullName).split(' ').filter(Boolean);
                const bTok = clean(baseTeamName).split(' ').filter(Boolean);
                let i = 0;
                while (i < fTok.length && i < bTok.length && fTok[i] === bTok[i]) i++;
                const origParts = (sideFullName ?? '').toString().trim().split(/\s+/);
                const s = origParts.slice(i).join(' ').trim();
                return s || (sideFullName ?? '').toString().trim();
            };

            // 1) Away/home
            const managedTeam = clean(tp['Team Name']);
            const tpAway = clean(tp['Away Team']);
            const shouldAway = managedTeam && tpAway === managedTeam;
            const oldAway = !!jx.AwayCheckbox;
            this.form.AwayCheckbox = shouldAway;
            if (oldAway !== shouldAway) {
                this.updatedFields.AwayCheckbox = true;
                changes.push(`Vierasottelu: ${oldAway ? '✓' : '—'} → ${shouldAway ? '✓' : '—'}`);
            }
            const isAway = this.form.AwayCheckbox;

            // 2) Time / date / location
            mark('game_start_time', 'Aloitusaika', jx.game_start_time, tp.Time ?? '');
            mark('game_date',       'Pvm',         jx.game_date,       tp.Date ?? '');
            mark('game_location',   'Paikka',      jx.game_location,   tp.Location ?? '');

            // 3) Opponent
            const opponentFromTP = isAway ? (tp['Home Team'] ?? '') : (tp['Away Team'] ?? '');
            mark('guest_team', 'Vastustaja', jx.guest_team, opponentFromTP);

            console.log('--- compareUpdates debug ---');
            console.log('opponentFromTP:', opponentFromTP, 'jx.guest_team:', jx.guest_team);
            console.log('cleaned:', clean(opponentFromTP), clean(jx.guest_team));
            console.log('hometeam:', tp['Home Team'], 'awayteam:', tp['Away Team'], 'isAway:', isAway);

            // 4) HomeTeamTextbox: alias pitää löytyä kokonaisena sanana, min 3 merkkiä
            const sideName = isAway ? (tp['Away Team'] ?? '') : (tp['Home Team'] ?? '');
            const alias = (jx.HomeTeamTextbox ?? '').toString().trim();

            const aliasNorm = clean(alias);
            const sideWords = clean(sideName).split(' ').filter(Boolean);
            const aliasOk = alias && aliasNorm.length >= 3 && sideWords.includes(aliasNorm);

            if (alias && !aliasOk) {
                this.updatedFields.HomeTeamTextbox = true;
                changes.push(`Joukkueen lisänimi taitaa olla väärin`);
                this.form.HomeTeamTextbox = alias; // käyttäjä korjaa itse
            } else {
                this.form.HomeTeamTextbox = alias;
            }

            // 5) Summary
            if (changes.length) {
                const tone = this.updatedFields.HomeTeamTextbox ? 'warning' : 'info';
                this.showToast('Ehdotetut muutokset:\n• ' + changes.join('\n• '), tone, 7000);
            } else {
                this.showToast('Tiedot ovat ajan tasalla.', 'info', 2500);
            }
            },

          

          // Kun käyttäjä muokkaa sisältöä, päivitetään Vue data
        syncContent(event) {
            event.target.innerHTML = this.form.game_public_info; // Kopioidaan alkuperäinen sisältö DOMiin
        },
        

        // Lähetä tiedot backendille päivitystä varten
        updateJopox() {

            this.isLoading = true;
            // Päivitetään `game_public_info` contenteditable-divistä ennen lomakkeen lähetystä
            const contentDiv = document.getElementById("public_info");
            if (contentDiv) {
                this.form.game_public_info = contentDiv.innerHTML.trim(); // Trim helpottaa tyhjien rivien käsittelyä
            }

            const selectedGroupIds = new Set(Array.isArray(this.form.selected_game_group_ids) ? this.form.selected_game_group_ids : []);
            const gameGroupsPayload = Array.isArray(this.form.game_groups)
                ? this.form.game_groups.map(group => ({ ...group, checked: selectedGroupIds.has(group?.id) }))
                : [];
            this.form.game_groups = gameGroupsPayload;

            const formWithStringCheckbox = {
                ...this.form,
                AwayCheckbox: this.form.AwayCheckbox ? 'on' : '',
                game_groups: gameGroupsPayload,
                
                
            };

            


            const payload = {
                game: this.selectedGame, // Tulospalvelun tiedot
                best_match: this.selectedGame.best_match, // Jopoxin tiedot
                updatedFields: this.updatedFields, // Päivitetyt kentät
                form: formWithStringCheckbox // Lomakkeen tiedot with string AwayCheckbox
            };
            console.log('Payload:', payload)
            fetch('/api/update_jopox', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            .then(response => response.json())
            .then(data => {
                this.showToast('Jopox-päivitys onnistui.', 'success', 3000);
                this.closeUpdateModal(); // Sulje modal päivityksen jälkeen
            })
            .catch(error => {
                console.error('Virhe Jopox-päivityksessä:', error);
                this.showToast('Päivityksessä tapahtui virhe.', 'error', 3000);
            });
            this.fetchGamesAndCompare();
        },

        createJopox(game) {
            try {
                this.isLoading = true;
                this.selectedGame = game;
                const payload = {
                    items: [
                        {
                            game
                        }
                    ]
                };

                fetch('/api/create_jopox', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                })
                .then(r => r.json())
                .then(res => {
                    const itemsArr = Array.isArray(res?.items) ? res.items : [];
                    const okCount = itemsArr.filter(i => i.status === 'ok').length;
                    const failCount = itemsArr.length > 0 ? (itemsArr.length - okCount) : 0;

                    if (failCount === 0 && okCount > 0) {
                        this.showToast('Ottelu lisätty Jopoxiin.', 'success', 3000);
                    } else if (failCount > 0) {
                        this.showToast('Ottelun luonti vaati tarkennusta tai epäonnistui.', 'warning', 7000);
                        console.log('create_jopox response (single):', res);
                    } else {
                        this.showToast('Palvelin ei palauttanut odotettua vastausta.', 'error', 4000);
                    }

                    return this.fetchGamesAndCompare();
                })
                .catch(err => {
                    console.error('Jopox-lisäys epäonnistui:', err);
                    this.showToast('Jopox-lisäys epäonnistui.', 'error', 4000);
                    this.fetchGamesAndCompare();
                });
            } catch (e) {
                console.error('createJopox error:', e);
                this.showToast('Jopox-lisäys epäonnistui.', 'error', 4000);
                this.fetchGamesAndCompare();
            }
        },

        // Sulje Päivitä Jopox -modal
        closeUpdateModal() {
            this.showUpdateJopoxModal = false;
            this.selectedGame = null;
        },

        formatReason(reason) {
            if (reason) {
                // Replace ". " with a line break
                return reason.replace(/\. /g, '<br>');
            }
            return '';
        },


        submitForm() {
            // Handle form submission logic here
            this.updateJopox()
            this.closeUpdateModal();
        },

        showToast(message, type = 'success', ms = 3000) {
            // pysy reaktiivisena: päivitä kentät, älä korvaa koko objektia
            if (this.toastTimer) clearTimeout(this.toastTimer);
          
            // sulje, jotta animaatio ja ajastin varmasti resetöityvät
            this.toast.show = false;
          
            this.toast.message = message;
            this.toast.type = type;
          
            // odota yksi "tick" ja näytä
            this.$nextTick(() => {
              this.toast.show = true;
              this.toastTimer = setTimeout(() => { this.toast.show = false; }, ms);
            });
        }






        
    },
    
    computed: {
        groupedGames() {
            const groups = {};
        
            this.filteredGames.forEach(game => {
                const date = game.SortableDate; // Use SortableDate for grouping
                if (!groups[date]) {
                    groups[date] = [];
                }
                groups[date].push(game);
            });
        
            return groups;
        },

        toastVariant() {
            const t = (this.toast?.type || 'success');
            return {
              isSuccess: t === 'success',
              isWarning: t === 'warning',
              isError:   t === 'error',
              isInfo:    t === 'info',
            };
          },

          toastToneClass() {
            return {
              'is-success': this.toastVariant.isSuccess,
              'is-warning': this.toastVariant.isWarning,
              'is-error':   this.toastVariant.isError,
              'is-info':    this.toastVariant.isInfo,
            };
          },

          bulkEligibleCount() {
            if (!Array.isArray(this.filteredGames) || this.filteredGames.length === 0) return 0;
            const eligible = this.filteredGames.filter(g => {
              const managed = this.managedTeams.some(t => t.team_id === g['Team ID']);
              const notPast = !this.isPastDay(g.SortableDate);
              const isRed = (g.match_status === 'red');
              return managed && notPast && isRed;
            });
            return eligible.length;
          },

          disableBulkButton() {
            return !this.hasJopox || this.isBulkCreating || this.bulkEligibleCount === 0;
          }
    },
    
    
    mounted() {

        fetch('/api/jopox_status')
        .then(r => r.json())
        .then(s => {
            this.hasJopox = !!(s && s.active);
            if (!this.hasJopox) {
              this.showToast(
                'Jopox ei ole aktivoitu. ' + 
                '<br><a href="/dashboard" style="color: lightblue; font-weight: bold;">Aktivoi Jopox täällä</a>.', 
                'warning', 
                7000
              );
            }
        })
        
        .finally(() => {
          // 2) hae loput normaalisti
          this.fetchTeams();
          this.fetchGamesAndCompare();
        });
    
    
    },

template: 



`
<div class="container my-4">
    <div>
        <h1>Valittujen joukkueiden ohjelma Tulospalvelusta.</h1>
        <p> Tässä näkymässä esitetään oletuksena hallinnoimiesi joukkueiden otteluohjelma.</p>
        <p> Valitse näytettävät joukkueet painikkeista.</p>
    </div>
</div>

    
    <!-- Sticky Team Selector -->
<div class="sticky-team-selector">              
    <!-- Managed Teams -->
    <h1>Hallinnoimasi joukkueet</h1>
    <div class="btn-group">
        <button
            v-for="team in managedTeams"
            :key="team.team_id"
            @click="toggleTeam(team.team_id)"
            :style="{
                backgroundColor: getButtonColor(team.team_name),
                color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_id)),
                }"
            :class="['btn', isTeamSelected(team.team_id) ? 'selected-team' : 'unselected-team']"
        >
            {{ team.team_name }} - {{ team.stat_group}}
        </button>
    </div>

   
    
    <!-- Followed Teams -->
    <h1 v-if="followedTeams.length > 0">Seuraamasi joukkueet</h1>
    <div class="btn-group">
        <button
            v-for="team in followedTeams"
            :key="team.team_id"
            @click="toggleTeam(team.team_id)"
            :style="{
                backgroundColor: getButtonColor(team.team_name),
                color: getTextColor(getButtonColor(team.team_name), isTeamSelected(team.team_id)),
            }"
            :class="['btn', isTeamSelected(team.team_id) ? 'selected-team' : 'unselected-team']"
        >
            {{ team.team_name }} - {{ team.stat_group}}
        </button>
    </div> 
    <div>
        <button class toggle-played-button @click="togglePlayedGames">
            {{ showPlayedGames ? "Piilota pelatut" : "Näytä pelatut" }}
        </button>
        <button class="bulk-create-button" :disabled="disableBulkButton" @click="bulkCreateJopox">
            {{ isBulkCreating ? 'Lisätään…' : 'Lisää kaikki Jopoxiin' }}
        </button>
    </div>
</div>


<div v-if="isLoading" id="loadingIndicator" class="loading-overlay is-visible" aria-hidden="true">
  <div class="loading-box">
    <div class="spinner-border text-secondary loading-spinner" role="status" aria-label="Loading"></div>
    <div class="loading-text">Ladataan…</div>
  </div>
</div>




<teleport to="body">
  <div class="igm-toast-container">
    <transition name="igmtoast">
      <div
        v-if="toast.show"
        class="igm-toast"
        :class="toastToneClass"
        role="status" aria-live="polite" aria-atomic="true"
      >
        <div class="igm-toast__inner">
          <div class="igm-toast__icon"
               v-html="toastVariant.isSuccess ? icons.check
                        : (toastVariant.isWarning ? icons.warn : icons.error)">
          </div>

          <!-- Sisältö: otsikko + viesti -->
          <div class="igm-toast__content">
            <div class="igm-toast__message" v-html="toast.message"></div>
          </div>

          <!-- Sulje oikeaan yläkulmaan -->
          <button type="button" class="igm-toast__close"
                  @click="toast.show=false" aria-label="Sulje">×</button>
        </div>
      </div>
    </transition>
  </div>
</teleport>





<div
    v-for="(games, date) in groupedGames"
    :key="date"
    class="game-window"
>
    <!-- Card Header -->
    <div 
        class="window-header"
        :class="{ 'past-day': isPastDay(date) }"
    >
        {{ getDayName(date) }} {{ games[0].Date }}
    </div>

    <!-- Game Info Cards -->
    <div class="game-cards">

    <div
        v-for="game in games"
        :key="game['Game ID'] + '-' + game['Team ID']"
        class="game-card"
        :style="getRowStyle(game)"
        @click="toggleGameDetails(game['Game ID'])"
    >
    
        <div class="gameInfo1">
            <div class="topRow">
                <p class="gameTeams">
                    {{ game['Home Team'] }} - {{ game['Away Team'] }}
                    <span v-if="game['Small Area Game'] === '1'">(Pienpeli)</span>
                </p>
                
                <button class="update-jopox-btn"
                    v-if="hasJopox && !isPastDay(date) && !isNotManagedTeam(game)"
                    @click.stop="game.match_status === 'red' ? createJopox(game) : openUpdateModal(game)">
                    <span class="status-text">
                        {{ game.match_status === 'red' ? 'Luo Jopoxiin' : 'Päivitä Jopox' }}
                    </span>
                </button>

                <div class="status-box"
                     v-if="hasJopox && !isPastDay(date) && !isNotManagedTeam(game)"
                     @click.stop="toggleModal($event, game.reason)"
                >
                    <span class="status-text">Jopox:</span>
                    <!-- Circle to indicate game status -->
                    <span
                        class="status-circle"
                        :class="{
                            'circle-green': game.match_status === 'green',
                            'circle-yellow': game.match_status === 'yellow',
                            'circle-red': game.match_status === 'red',
                        }"
                    ></span>
                </div>
            </div>
            <div class="bottomRow">
                <p class="gameTime"> Klo {{ game.Time || 'Aika ei saatavilla' }}</p>
                <p class="gameLocation">{{ game.Location || 'Paikka ei saatavilla' }}</p>
                <p class="gameStatgroup" style="font-size: 75%;">{{ game['Stat Group Name'] }}</p>
            </div>

            <!-- Expanded Section for Jopox Details -->
            <div v-if="expandedGameId === game['Game ID']" class="game-details">
                <h2>Jopox tapahtuma:</h2>
                <p><strong>{{ game.best_match?.joukkueet|| 'Not available' }}</strong></p>
                <p><strong>Paikka:</strong> {{ game.best_match?.paikka || 'Not available' }}</p>
                <p><strong>Pvm:</strong> {{ game.best_match?.pvm || 'Not available' }}</p>
                <p><strong>Klo:</strong> {{ game.best_match?.aika || 'Not available' }}</p>
                <p><strong>Lisätiedot:</strong> 
                 {{ 
                    game.best_match 
                    ? (game.best_match.Lisätiedot || 'Lisätiedot eivät ole tässä kentässä saatavilla toistaiseksi. Voit tarkastaa lisätiedot painamalla "Päivitä Jopox" -painiketta.') 
                    : 'No additional details available' 
                }}
                </p>

                <div v-if="game.warning" class="warning-message">
                <strong>Varoitus:</strong> {{ game.warning }}
                </div>
            </div>
        </div>
    </div>
</div>
</div>

<!-- Modal -->
<div v-show="showReasonPopup" class="modal-window">
    <div class="modal-arrow"></div>
    <span class="modal-close" @click.stop="closeModal">&times;</span>
    <h1>Jopox huomiot:</h1>
    <p v-html="popupReason"></p>
</div>

<!-- Add this to your HTML or Vue template -->
<div v-if="showUpdateJopoxModal" class="modal-window2">
    <div class="modal-content">
        <div class="modal-close" @click="closeUpdateModal">&times;</div>
        <h2>Päivitä Jopox</h2>
        <form id="jpx-details-form">
            <!-- Sarja -->
            <div>
                <label for="league">Sarja:</label>
                <select id="league" v-model="form.league_selected">
                    <option 
                        v-for="option in form.league_options" 
                        :key="option.value" 
                        :value="option"
                    >
                        {{ option.text }}
                    </option>
                </select>
            </div>

            <!-- Kotijoukkue -->
            <div :class="{'updated-field': updatedFields.HomeTeamTextbox}">
                <label for="home_team">{{form.SiteNameLabel}}</label>
                <input type="text" id="home_team" v-model="form.HomeTeamTextbox" placeholder="Lisänimi (ei pakollinen)">
            </div>

            <!-- Vastustaja -->
            <div :class="{'updated-field': updatedFields.guest_team}">
                <label for="guest_team">Vastustaja:</label>
                <input type="text" id="guest_team" v-model="form.guest_team" placeholder="Vastustaja">
            </div>

            <!-- Vierasottelu -->
            <div>
                <label for="away_game">Vierasottelu:</label>
                <input type="checkbox" id="away_game" v-model="form.AwayCheckbox">
            </div>

            <!-- Paikka -->
            <div :class="{'updated-field': updatedFields.game_location}">
                <label for="location">Paikka:</label>
                <input type="text" id="location" v-model="form.game_location" placeholder="Paikka">
            </div>

            <!-- Päivämäärä -->
            <div :class="{'updated-field': updatedFields.game_date}">
                <label for="date">Pvm:</label>
                <input type="text" id="date" v-model="form.game_date" placeholder="Pvm">
            </div>

            <!-- Aloitusaika -->
            <div :class="{'updated-field': updatedFields.game_start_time}">
                <label for="start_time">Aloitusaika:</label>
                <input type="text" id="start_time" v-model="form.game_start_time" placeholder="Aloitusaika">
            </div>

            <!-- Kesto -->
            <div>
                <label for="duration">Kesto:</label>
                <input type="text" id="duration" v-model="form.game_duration" placeholder="Kesto (min)">
            </div>

            <!-- Ilmoittautumisdeadline -->
            <div>
                <label for="deadline_date">Ilmoittautumisdeadline Pvm:</label>
                <input type="text" id="deadline_date" v-model="form.deadline_date" placeholder="Pvm">
            </div>
            <div>
                <label for="deadline_time">Ilmoittautumisdeadline Klo:</label>
                <input type="text" id="deadline_time" v-model="form.deadline_time" placeholder="Klo">
            </div>

            <!-- Osallistujat -->
            <div>
                <label for="participants">Osallistujat:</label>
                <div v-for="group in form.game_groups" :key="group.id">
                    <input
                        type="checkbox"
                        :id="'gamegroup_' + group.id"
                        v-model="form.selected_game_group_ids"
                        :value="group.id"
                    >
                    <label :for="'gamegroup_' + group.id">{{ group.label }}</label>
                </div>
            </div>

            <!-- Ennakkoinfo -->
            <label for="public_info">Ennakkoinfo:</label>
            <div 
                id="public_info"
                contenteditable="true"
                class="editable-content"
            >
            </div>          
            <div class="button-container">
                <button class="cancel-button" type="button" @click="closeUpdateModal">Peruuta</button>
                <button class="action-button" type="button" @click="submitForm">Päivitä</button>
            </div>
        </form>
    </div>
</div>







`
});

// Mount the Vue app
app.mount('#schedule-app');
