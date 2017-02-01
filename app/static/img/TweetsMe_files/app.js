'use strict';   // See note about 'use strict'; below

var myApp = angular.module('myApp', ['ngRoute']);

// controller of the view
myApp.controller('profileCntlr',function($scope) {

  console.log("kelvin");
  $scope.search = '';

  $scope.$watch('search', function(newValue, oldValue) {
    console.log('new value is '+newValue);
  });


  // setTimeout(function() {
  //   $scope.lastName = 'smith';
  //   $scope.$apply();
  // },1000);

})






















myApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
    when('/user/info', {
      templateUrl: '/static/partials/user-info.html',
    }).
    when('/user/profile', {
      templateUrl: '/static/partials/user-profile.html',
    }).
    otherwise({
      redirectTo: '/'
    });
  }
]);