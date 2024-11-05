$(document).ready(function () {
   
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
                    
                    // Generate each <option> with the necessary data attributes
                    data.Teams.forEach(function (team) {
                        teamOptions += `<option value="${team.TeamID}" 
                                        data-abbrv="${team.TeamAbbrv || ''}" 
                                        data-association="${team.TeamAssociation || ''}" 
                                        data-img="${team.TeamImg || ''}"
                                        data-name="${team.TeamAbbrv || ''}" 
                                        data-statgroup="${selectedStatGroupName || ''}">
                                        ${team.TeamAbbrv}</option>`;
                    });
    
                    console.log('Generated team options HTML:', teamOptions); // Debugging: Check generated HTML
                    
                    // Populate the teams dropdown
                    $('#teams').html(teamOptions);
    
                    // Log each team option individually for verification
                    $('#teams option').each(function () {
                        console.log('Option value:', $(this).val(), 'data-abbrv:', $(this).data('abbrv'), 
                                    'data-association:', $(this).data('association'), 'data-img:', $(this).data('img'));
                    });
                }
            });
        }
    });
    
    
    $('#dashboardForm').submit(function (e) {
        e.preventDefault(); // Prevent default form submission
    
        const selectedTeams = [];
        const action = $(document.activeElement).val(); // Get the action from the clicked button
    
        // Collect selected teams and their information
        $('#teams option:selected').each(function () {
     
            selectedTeams.push({
                TeamID: $(this).val(),
                TeamAbbrv: $(this).data('abbrv'),        // Captures TeamAbbrv
                team_association: $(this).data('association'), // Captures TeamAssociation
                team_name: $(this).data('name'),
                stat_group: $(this).data('statgroup')
            });
        });
        console.log(selectedTeams); // This will confirm if the event is firing

        const data = {
            action: action,
            teams: selectedTeams,
            season: $('#season').val(),
            level_id: $('#levels').val(),
            statgroup: $('#statgroups').val()
        };
    
        // Send data as JSON to the update_teams route
        $.ajax({
            url: '/dashboard/update_teams',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function (response) {
                alert(response.message);
            },
            error: function (xhr) {
                alert('An error occurred: ' + xhr.responseText);
            }
        });
    });

    // Handle remove teams confirmation
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
                alert(response.message);
                location.reload(); // Reload the page to update the list of teams
            },
            error: function (xhr) {
                alert('An error occurred: ' + xhr.responseText);
            }
        });

        // Close the modal after submitting
        $('#removeTeamsModal').modal('hide');
    });
});

