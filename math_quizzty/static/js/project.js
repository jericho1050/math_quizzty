/* Project specific Javascript goes here. */
function confirmDelete(el) {
    Swal.fire({
        title: 'Delete Question',
        text: 'Are you sure you want to delete this question? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            htmx.trigger(el, 'deleteConfirmed');
            Swal.fire(
                'Deleted!',
                'Your question has been deleted.',
                'success'
            );
        }
    });
}