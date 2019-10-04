var app = angular.module('items', ['ngResource', 'ngGrid', 'ui.bootstrap']);

// Create a controller with name itemListController to bind to the grid section.
app.controller('itemsListController', function ($scope, $rootScope, itemService) {
    // Initialize required information: sorting, the first page to show and the grid options.
    $scope.sortInfo = {fields: ['id'], directions: ['asc']};
    $scope.items = {currentPage: 1};

    $scope.gridOptions = {
        data: 'items.list',
        useExternalSorting: true,
        sortInfo: $scope.sortInfo,


        columnDefs: [
            { field: 'id', displayName: 'Id' },
            { field: 'description', displayName: 'Description' },
            { field: 'done', displayName: 'Done' },
            { field: '', width: 30, cellTemplate: '<span class="glyphicon glyphicon-remove remove" ng-click="deleteRow(row)"></span>' }
        ],

        multiSelect: false,
        selectedItems: [],
        // Broadcasts an event when a row is selected, to signal the form that it needs to load the row data.
        afterSelectionChange: function (rowItem) {
            if (rowItem.selected) {
                $rootScope.$broadcast('itemselected', $scope.gridOptions.selectedItems[0].id);
            }
        }
    };

    // Refresh the grid, calling the appropriate rest method.
    $scope.refreshGrid = function () {
        var listitemsArgs = {
            page: $scope.items.currentPage,
            sortFields: $scope.sortInfo.fields[0],
            sortDirections: $scope.sortInfo.directions[0]
        };

        itemService.get(listitemsArgs, function (data) {
            $scope.items = data;
        })
    };

    // Broadcast an event when an element in the grid is deleted. No real deletion is perfomed at this point.
    $scope.deleteRow = function (row) {
        $rootScope.$broadcast('deleteitem', row.entity.id);
    };

    // Watch the sortInfo variable. If changes are detected than we need to refresh the grid.
    // This also works for the first page access, since we assign the initial sorting in the initialize section.
    $scope.$watch('sortInfo.fields[0]', function () {
        $scope.refreshGrid();
    }, true);
    $scope.$watch('sortInfo.directions[0]', function () {
        $scope.refreshGrid();
    }, true);

    // Do something when the grid is sorted.
    // The grid throws the ngGridEventSorted that gets picked up here and assigns the sortInfo to the scope.
    // This will allow to watch the sortInfo in the scope for changed and refresh the grid.
    $scope.$on('ngGridEventSorted', function (event, sortInfo) {
        $scope.sortInfo = sortInfo;
    });

    // Picks the event broadcasted when a item is saved or deleted to refresh the grid elements with the most
    // updated information.
    $scope.$on('refreshGrid', function () {
        $scope.refreshGrid();
    });

    // Picks the event broadcasted when the form is cleared to also clear the grid selection.
    $scope.$on('clear', function () {
        $scope.gridOptions.selectAll(false);
    });
});

// Create a controller with name itemsFormController to bind to the form section.
app.controller('itemsFormController', function ($scope, $rootScope, itemService) {
    // Clears the form. Either by clicking the 'Clear' button in the form, or when a successful save is performed.
    $scope.clearForm = function () {
        $scope.item = null;
        // Resets the form validation state.
        $scope.itemForm.$setPristine();
        // Broadcast the event to also clear the grid selection.
        $rootScope.$broadcast('clear');
    };

    // Calls the rest method to save a item.
    $scope.updateItem = function () {
        itemService.save($scope.item).$promise.then(
            function () {
                // Broadcast the event to refresh the grid.
                $rootScope.$broadcast('refreshGrid');
                // Broadcast the event to display a save message.
                $rootScope.$broadcast('itemsaved');
                // XXX Generates null error in browser ?!?
                $scope.clearForm();
            },
            function () {
                // Broadcast the event for a server error.
                $rootScope.$broadcast('error');
            });
    };

    // Picks up the event broadcasted when the item is selected from the grid and perform the item load by calling
    // the appropiate rest service.
    $scope.$on('itemselected', function (event, id) {
        $scope.item = itemService.get({id: id});
    });

    // Picks us the event broadcasted when the item is deleted from the grid and perform the actual item delete by
    // calling the appropiate rest service.
    $scope.$on('deleteitem', function (event, id) {
        itemService.delete({id: id}).$promise.then(
            function () {
                // Broadcast the event to refresh the grid.
                $rootScope.$broadcast('refreshGrid');
                // Broadcast the event to display a delete message.
                $rootScope.$broadcast('itemDeleted');
                $scope.clearForm();
            },
            function () {
                // Broadcast the event for a server error.
                $rootScope.$broadcast('error');
            });
    });
});

// Create a controller with name alertMessagesController to bind to the feedback messages section.
app.controller('alertMessagesController', function ($scope) {
    // Picks up the event to display a saved message.
    $scope.$on('itemSaved', function () {
        $scope.alerts = [
            { type: 'success', msg: 'Record saved successfully!' }
        ];
    });

    // Picks up the event to display a deleted message.
    $scope.$on('itemDeleted', function () {
        $scope.alerts = [
            { type: 'success', msg: 'Record deleted successfully!' }
        ];
    });

    // Picks up the event to display a server error message.
    $scope.$on('error', function () {
        $scope.alerts = [
            { type: 'danger', msg: 'There was a problem in the server!' }
        ];
    });

    $scope.closeAlert = function (index) {
        $scope.alerts.splice(index, 1);
    };
});

// Service that provides items operations
app.factory('itemService', function ($resource) {
    return $resource('http://api.lab.example.com:30080/todo/api/items/:id');
});


// Create a controller that handles host information
app.controller('hostController', function ($scope, hostService) {
        $scope.host = hostService.get();
});

//Service that provides host operations
app.factory('hostService', function ($resource) {
    return $resource('http://api.lab.example.com:30080/todo/api/host', null,
                {
                'get': { method:'GET' }
                });
});
