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
                        
                    // Populate the teams dropdown
                    $('#teams').html(teamOptions);
                }
            });
        }
    });
    
    
// Function to load the latest teams data from the server
function loadTeams() {
    return $.ajax({
        url: '/dashboard/get_ManagedFollowed', // Assumes a backend endpoint to fetch the latest teams data
        method: 'GET',
        success: function (response) {
            console.log('Hallinnoidut joukkueet:', response);
            // Update the managed teams list
            const managedTeamsList = $('#managedTeamsList');
            managedTeamsList.empty();
            response.managed_teams.forEach(team => {
                managedTeamsList.append(`<li data-team-id="${team.team_id}">${team.team_name} (${team.stat_group})</li>`);
            });

            // Update the followed teams list
            const followedTeamsList = $('#followedTeamsList');
            followedTeamsList.empty();
            response.followed_teams.forEach(team => {
                followedTeamsList.append(`<li data-team-id="${team.team_id}">${team.team_name} (${team.stat_group})</li>`);
            });

            // Store the jopox managed team in a variable
            const jopoxManagedTeam = response.jopox_managed_team;

            // Update the HTML element with the jopox managed team
            // Update the HTML element with the jopox managed team
            if (jopoxManagedTeam) {
                $('#jopoxManagedTeam').text(jopoxManagedTeam);
            } else {
                $('#jopoxManagedTeam').text('Et hallinnoi tällä hetkellä mitään Jopox-joukkuetta.');
            }

            // Update modal with the latest data
            updateRemoveTeamsModal(response.managed_teams, response.followed_teams, response.jopox_managed_team);
        },
        error: function (xhr) {
            console.error("Error fetching teams:", xhr.responseText);
        }
    });
}

// Function to update Remove Teams Modal content
function updateRemoveTeamsModal(managedTeams, followedTeams, jopoxManagedTeam) {
    const managedTeamsModalList = $('#removeTeamsModal .modal-body ul:eq(1)');
    const followedTeamsModalList = $('#removeTeamsModal .modal-body ul:eq(2)');
    const jopoxManagedModalTeam = $('#removeTeamsModal .modal-body ul:eq(0)');

    jopoxManagedModalTeam.empty();
    managedTeamsModalList.empty();
    followedTeamsModalList.empty();

    // Append the Jopox managed team
    if (jopoxManagedTeam) {
        jopoxManagedModalTeam.append(`
            <li>
                <input type="checkbox" name="teams" value="${jopoxManagedTeam}" data-relationship="jopox">
                ${jopoxManagedTeam}
            </li>
        `);
    } else {
        jopoxManagedModalTeam.append('<p>No Jopox managed team available.</p>');
    }

    // Append the managed teams
    managedTeams.forEach(team => {
        managedTeamsModalList.append(`
            <li>
                <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="manage">
                ${team.team_name} (Stat Group: ${team.stat_group})
            </li>
        `);
    });

    // Append the followed teams
    followedTeams.forEach(team => {
        followedTeamsModalList.append(`
            <li>
                <input type="checkbox" name="teams" value="${team.team_id}" data-relationship="follow">
                ${team.team_name} (Stat Group: ${team.stat_group})
            </li>
        `);
    });
}

// Trigger change to pre-populate levels when the page loads
$('#season').trigger('change');

// Load latest teams initially
loadTeams();

// Handle add/update teams submission
$('#dashboardForm').submit(function (e) {
    e.preventDefault();

    const selectedTeams = [];
    const action = $(document.activeElement).val(); // Get the value of the active element (button pressed)
    console.log('Action:', action); // Log the action
    $('#teams option:selected').each(function () {
        selectedTeams.push({
            TeamID: $(this).val(),
            TeamAbbrv: $(this).data('abbrv'),
            team_association: $(this).data('association'),
            team_name: $(this).data('name'),
            stat_group: $(this).data('statgroup'),
            season: $('#season').val(),
            level_id: $('#levels').val(),
            statgroup: $('#statgroups').val()    
        });
    });

    const data = {
        action: action,
        teams: selectedTeams,
    };

    console.log('Form data:', data); // Log form data

    $.ajax({
        url: '/dashboard/update_teams',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (response) {
            console.log('Success:', response); // Log success response
            loadTeams(); // Refresh lists and modal with latest data after update
        },
        error: function (xhr) {
            alert('An error occurred: ' + xhr.responseText);
        }
    });
});

//this is a selector for user to select the jopox teamid from the dropdown that is submitted to backend for his user profile
$('#jopox_teamidselector').submit(function () {
    event.preventDefault();
    const jopoxTeamId = $('#jopox_team_id').val();
    const jopoxTeamName = $('#jopox_team_id option:selected').text();
    console.log('jopoxTeamId:', jopoxTeamId);
    console.log('jopoxTeamName:', jopoxTeamName);
    $.ajax({
        url: '/dashboard/select_jopox_team',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ jopoxTeamId: jopoxTeamId, jopoxTeamName: jopoxTeamName }),
        success: function (response) {
            console.log('Success:', response);
        },
        error: function (xhr) {
            alert('An error occurred: ' + xhr.responseText);
        }
    });
    if (!jopoxTeamId) {
        alert('Valitse joukkue ennen lähettämistä.');
        return;
    }
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

            loadTeams(); // Refresh lists and modal with latest data after removal

            // Close the modal
            $('#removeTeamsModal').modal('hide');
        },
        error: function (xhr) {
            alert('An error occurred: ' + xhr.responseText);
        }
    });
});

// Re-fetch and update modal content each time it opens to ensure fresh data
$('#removeTeamsModal').on('show.bs.modal', function () {
    loadTeams(); // Fetch the latest data to populate the modal
});
});

