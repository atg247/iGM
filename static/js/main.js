$(document).ready(function () {
    let isHighlightOn = false; // Initialize this variable here
    let selectedTeamsList = []; // Initialize selectedTeamsList as an empty array

    // Helper function to check if two rinks are equivalent based on prefix length
    function areRinksEquivalent(rinkA, rinkB) {
        const prefixLength = 3;
        return rinkA.substring(0, prefixLength).toLowerCase() === rinkB.substring(0, prefixLength).toLowerCase();
    }   
    // Fetch levels based on season selection
    $('#season').change(function () {
        const season = $(this).val();
        if (season) {
            $.get(`/gamefetcher/get_levels/${season}`, function (data) {
                let levelOptions = '<option value="">Valitse taso</option>';
                data.forEach(function (level) {
                    levelOptions += `<option value="${level.LevelID}">${level.LevelName}</option>`;
                });
                $('#levels').html(levelOptions);
                $('#statgroups').html('<option value="">Valitse sarja/lohko</option>');
                $('#teams').html('<option value="">Valitse joukkueet</option>');
            });
        }
    });

    // Trigger change to pre-populate levels when the page loads
    $('#season').trigger('change');

    // Fetch stat groups based on level selection
    $('#levels').change(function () {
        const levelId = $(this).val();
        const season = $('#season').val();
        if (levelId) {
            $.get(`/gamefetcher/get_statgroups/${season}/${levelId}/0`, function (data) {
                let statGroupOptions = '<option value="">Valitse sarja/lohko</option>';
                data.forEach(function (statGroup) {
                    statGroupOptions += `<option value="${statGroup.StatGroupID}">${statGroup.StatGroupName}</option>`;
                });
                $('#statgroups').html(statGroupOptions);
                $('#teams').html('<option value="">Valitse joukkueet</option>');
            });
        }
    });

    // Fetch teams based on stat group selection
    $('#statgroups').change(function () {
        const statGroupId = $(this).val();
        const season = $('#season').val();
        let selectedStatGroupName = $('#statgroups option:selected').text(); // Get selected stat group name

        if (statGroupId) {
            $.get(`/gamefetcher/get_teams/${season}/${statGroupId}`, function (data) {
                if (Array.isArray(data.Teams)) {
                    let teamOptions = '';
                    data.Teams.forEach(function (team) {
                        teamOptions += `<option value="${team.TeamID}" data-statgroup="${selectedStatGroupName}">${team.TeamAbbrv}</option>`;
                    });
                    $('#teams').html(teamOptions);
                }
            });
        }
    });

    // Function to update selectedTeamsList
    function updateSelectedTeamsList() {
        let newSelectedTeams = $('#teams').find('option:selected');
        let newTeamEntries = [];

        newSelectedTeams.each(function () {
            let teamName = $(this).text();
            let statGroupName = $(this).data('statgroup'); // Get the stat group name from the data attribute
            let formattedTeamName = `${teamName} : (${statGroupName})`;

            if (!selectedTeamsList.includes(formattedTeamName)) {
                newTeamEntries.push(formattedTeamName);
                }
        });

        selectedTeamsList = selectedTeamsList.concat(newTeamEntries);

        if (newTeamEntries.length > 0) {
            newTeamEntries.forEach(teamEntry => {
                $('#teamsNames').append($('<div>').text(teamEntry));
            });
            
            // Show the selected teams container if there are new entries
            $('#selectedTeamsList').show();
        } else if (selectedTeamsList.length === 0) {
            // Hide the selected teams container if there are no teams in the list
            $('#selectedTeamsList').hide();
        }
    }

    let allGamesData = [];

    // Submit form and fetch games data
    $('#fetchForm').on('submit', function (event) {
        event.preventDefault();

        updateSelectedTeamsList();

        const formData = $(this).serialize();

        $.post('/gamefetcher/fetch_games', formData, function (data) {
            console.log("fetch_games started:", data);

            if (data.error) {
                alert(data.error);
                return;
            }
                
            // Filter out duplicate games using Game ID
            const seenGameIds = new Set(allGamesData.map(game => game['Game ID']));
            const uniqueGames = data.filter(function (game) {
                if (!seenGameIds.has(game['Game ID'])) {
                    seenGameIds.add(game['Game ID']);
                    return true;
                }
                return false;
            });

                // Check if there are new games to add
            if (uniqueGames.length > 0) {
                // Update date formatting for the unique games
                uniqueGames.forEach(function (game) {
                    if (game.Date) {
                        const dateObj = new Date(game.Date);
                        if (!isNaN(dateObj)) {
                            const day = String(dateObj.getDate()).padStart(2, '0');
                            const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                            const year = dateObj.getFullYear();
                            game.Date = `${day}.${month}.${year}`;
                            game.SortableDate = dateObj;
                    }
                }
            });
            // Concatenate unique games to the existing list of games
            allGamesData = allGamesData.concat(uniqueGames);

            // Clear and destroy existing DataTable instance if it exists
            if ($.fn.DataTable.isDataTable('#gamesTable')) {
                $('#gamesTable').DataTable().clear().destroy();
            }

            // Reinitialize the DataTable with the updated data
            $('#gamesTable').DataTable({
                data: allGamesData,
                columns: [
                    {
                        data: 'Game ID',
                        render: function (data) {
                            return `<input type="checkbox" name="game_selection" value="${data}">`;
                        }
                    },
                    { data: 'Team ID' },
                    { data: 'Game ID' },
                    {
                        data: 'SortableDate',
                        render: function (data, type, row) {
                            if (type === 'display' || type === 'filter') {
                                return row.Date;
                            }
                            return data;
                        }
                    },
                    { data: 'Time' },
                    { data: 'Home Team' },
                    { data: 'Away Team' },
                    { 
                        data: 'Small Area Game',
                        render: (data) => data === '1' ? 'p' : ' '
                    },
                    { data: 'Home Goals' },
                    { data: 'Away Goals' },
                    { data: 'Location' },
                    { data: 'Level Name' }
                ],
                ordering: true,
                order: [[3, "asc"]],
                paging: false,
                searching: false,
                info: true,
            });
        }
        }).fail(function () {
            alert('Unexpected response format. Please try again.');
        });
    });
       //--------------------------------------------------//
    // Add styles for highlighting
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            .highlight-same-day {
                background-color: #ffff99 !important;
            }
            .highlight-orange {
                background-color: #ffa500 !important;
            }
            .highlight-red {
                background-color: #ff4c4c !important;
            }
            .highlight-selected {
                background-color: #87CEFA !important; /* Light blue to indicate the highlighted rows */
            }
        `)
        .appendTo('head');

    // Highlight overlap button functionality
    $('#highlightButton').click(function () {
        let table = $('#gamesTable').DataTable();
    
        if (isHighlightOn) {
            table.rows().nodes().each(function (row) {
                $(row).find('td:eq(3)').removeClass('highlight-same-day highlight-orange highlight-red');
            });
    
            $('#highlightButton').text('Korosta päällekkäiset');
            isHighlightOn = false;
        } else {
            let dateGroups = {};
    
            // Group rows by date
            table.rows().every(function () {
                let data = this.data();
                let date = data.Date;
    
                if (!dateGroups[date]) {
                    dateGroups[date] = [];
                }
                dateGroups[date].push(this.node());
            });
    
            // Extract team names from selectedTeamsList
            let selectedTeamNames = selectedTeamsList.map(entry => entry.split(' : ')[0]);
    
            // Iterate through each date group
            $.each(dateGroups, function (date, rows) {
                if (rows.length > 1) {
                    let rinkGroups = {};
                    let selectedTeamsPlaying = 0;
                    console.log('Selected Teams List:', selectedTeamsList);
    
                    rows.forEach(function (row) {
                        let rink = $(row).find('td:eq(10)').text(); // Assuming rink info is in column 9
                        let homeTeam = $(row).find('td:eq(5)').text(); // Assuming home team is in column 5
                        let awayTeam = $(row).find('td:eq(6)').text(); // Assuming away team is in column 6
    
                        // Debugging statements
                        console.log(`Home Team: ${homeTeam}`);
                        console.log(`Away Team: ${awayTeam}`);
    
                        // Count how many selected teams are playing on that date
                        if (Array.isArray(selectedTeamNames) && (selectedTeamNames.includes(homeTeam) || selectedTeamNames.includes(awayTeam))) {
                            selectedTeamsPlaying++;
                        }
    
                        // Group rows by rink
                        let foundEquivalentRink = false;
                        for (let normalizedRink in rinkGroups) {
                            if (areRinksEquivalent(normalizedRink, rink)) {
                                rinkGroups[normalizedRink].push(row);
                                foundEquivalentRink = true;
                                break;
                            }
                        }
                        if (!foundEquivalentRink) {
                            rinkGroups[rink] = [row];
                        }
                    });
    
                    let uniqueRinksCount = Object.keys(rinkGroups).length;
    
                    // Debugging statements
                    console.log(`Date: ${date}`);
                    console.log(`Selected Teams Playing: ${selectedTeamsPlaying}`);
                    console.log(`Unique Rinks Count: ${uniqueRinksCount}`);
                    console.log(`Rink Groups:`, rinkGroups);
        
                    // Apply different highlights based on the conditions
                    if (selectedTeamsPlaying >= 3 && uniqueRinksCount > 2) {
                        rows.forEach(function (row) {
                            $(row).find('td:eq(3)').addClass('highlight-red');
                        });
                    } else if (selectedTeamsPlaying >= 3 && uniqueRinksCount > 1) {
                        rows.forEach(function (row) {
                            $(row).find('td:eq(3)').addClass('highlight-orange');
                        });
                    } else {
                        rows.forEach(function (row) {
                            $(row).find('td:eq(3)').addClass('highlight-same-day');
                        });
                    }
                }
            });
    
            $('#highlightButton').text('Älä näytä päällekkäisiä');
            isHighlightOn = true;
        }
    });

    // Clear button functionality
    $('#clear').click(function () {
        if ($.fn.DataTable.isDataTable('#gamesTable')) {
            $('#gamesTable').DataTable().clear().destroy();
        }
        allGamesData = [];
        selectedTeamsList = [];
        $('#selectedTeamsList').hide();
        $('#teamsNames').empty();
        $('#highlightButton').text('Korosta päällekkäiset');
        isHighlightOn = false;
    });
// Function to remove selected teams
$('#confirmRemoveTeams').click(function () {
    const selectedTeams = [];

    // Collect selected teams with their relationship type
    $('#removeTeamsForm input[name="teams"]:checked').each(function () {
        selectedTeams.push({
            team_id: $(this).val(),
            relationship_type: $(this).data('relationship')
        });
    });

    // Send the selected teams to the server
    $.ajax({
        url: '/dashboard/remove_teams',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ teams: selectedTeams }),
        success: function (response) {
            loadTeams(); // Refresh lists and modal with latest data after removal

            // Close the modal
            $('#removeTeamsModal').modal('hide');
        },
        error: function (xhr) {
            alert('An error occurred: ' + xhr.responseText);
        }
    });
});

    $('#forwardGamesButton').click(function () {
        const selectedGames = [];

        $('#gamesTable input[name="game_selection"]:checked').each(function () {
            const row = $(this).closest('tr');
            const gameData = {
                game_id: $(this).val(),
                date: row.find('td:eq(3)').text(),
                time: row.find('td:eq(4)').text(),
                home_team: row.find('td:eq(5)').text(),
                away_team: row.find('td:eq(6)').text(),
                SmallAreaGame: row.find('td:eq(7)').text(),
                home_goals: row.find('td:eq(8)').text(),
                away_goals: row.find('td:eq(9)').text(),
                location: row.find('td:eq(10)').text(),
                level_name: row.find('td:eq(11)').text()
            };
            selectedGames.push(gameData);
        });

        if (selectedGames.length === 0) {
            alert("No games selected. Please select at least one game.");
            return;
        }

        $.ajax({
            url: '/gamefetcher/send_selected_games',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ selected_games: selectedGames }),
            success: function (response) {
                if (response.error) {
                    alert(response.error);
                } else {
                    alert(response.message);
                }
            },
            error: function () {
                alert('Failed to forward the selected games. Please try again.');
            }
        });
}); 
}); 

