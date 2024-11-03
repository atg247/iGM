$(document).ready(function () {
    console.log("Document is ready.");

    // Bind the button click event
    $('#fetchEventsButton').on('click', function () {
        console.log("Fetch Events Button Clicked");

        // Use jQuery to submit the GET request
        $.get('/jopox_ottelut/hae_kalenteri', function (data) {
            if (data.error) {
                alert(data.error);
                return;
            }

            // Log the data to check the structure in the console
            console.log("Data received from server:", data);

            // Clear and destroy existing DataTable instance if it exists
            if ($.fn.DataTable.isDataTable('#JopoxGamesTable')) {
                $('#JopoxGamesTable').DataTable().clear().destroy();
            }
            data.forEach(function (game) {
                if (game.SortableDate) {
                    const dateObj = new Date(game.SortableDate);
                    if (!isNaN(dateObj)) {
                        // Format the display date to DD.MM.YYYY
                        const day = String(dateObj.getDate()).padStart(2, '0');
                        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                        const year = dateObj.getFullYear();
                        game.Pvm = `${day}.${month}.${year}`; // Human-readable date
                        game.SortableDate = dateObj; // Date object for sorting
                    }
                }
            });
            // Reinitialize the DataTable with the updated data
            $('#JopoxGamesTable').DataTable({
                data: data,
                columns: [
                    { data: 'SortableDate',  // Sorting field
                        render: function (data, type, row) {
                            if (type === 'display' || type === 'filter') {
                                return row.Pvm;  // Display the formatted date (DD.MM.YYYY)
                            }
                            return data;  // For sorting, use the actual SortableDate
                        }
                    },
                    { data: 'Tapahtuma' },
                    { data: 'Aika' },
                    { data: 'Paikka' },
                    { data: 'Lisätiedot', defaultContent: '-' }
                ],
                ordering: true,
                order: [[0, "asc"]],
                paging: false,
                searching: false,
                info: true,
                language: {
                    emptyTable: "No events available to display"
                }
            });
        }).fail(function () {
            alert('Unexpected response format. Please try again.');
        });
    });
});
