'use strict';

var myApp = angular.module('myApp', ['ngRoute', 'yaru22.angular-timeago','infinite-scroll','ngAnimate']);
angular.module('infinite-scroll').value('THROTTLE_MILLISECONDS', 1000)

var protocol = "https"
var host = "localhost"
var port = "80"
var api_version = "v1.0"
var apiBaseUrl = "/api/"+api_version
var allowedMimetype = ['image/jpeg','image/png'];
const POLLING_INTERVAL = 10000;
const TIMEOUT_LIMIT = 10000;
const POLL_TWEETS_LIMIT = 10;

var fontList = ['Abril Fatface','Arvo','Droid Sans','Josefin Slab','Lato','Old Standard TT','Open Sans','PT Sans','PT Serif','Ubuntu','Vollkorn'];
WebFont.load({
  google: {
    families: fontList
  }
});


var maxNewTweetMessageCharacters = 140;
var availableMoods = null;



myApp.controller('menuCntlr', function($scope, $http, $location, $route, $window) {
  console.log("sidebarCntlr started");

  angular.element('#userSearchConsole').search({
    apiSettings: {
      url: apiBaseUrl+"/user/search/{query}"
    },
    fields: {
      results: 'results',
      title: 'name',
      description: 'email',
      image: 'picture_url',
      action: 'action',
      actionURL: 'profile_url',
      actionText: 'action_text'
      // actionText: "email"
    },
    minCharacters: 1,
    transition: 'fade',
    duration: 300,
    maxResult: 5,
    showNoResults: true,
    selectFirstResult: true,
    onSelect: function(result, response) {
      // redirect user to the profile of the selected user
      // console.log(result);
      $location.path('/user/'+result.user_id+"/profile").replace();
      $scope.$apply();

    },
  });

  $scope.toggleNewTweetModal = function() {
    // console.log('click');
    angular.element('#newTweetModal')
      .modal({
        closable: true,
        blurring: false,
      })
      .modal('show');

    // setup emoji picker
    var emojiPicker = new EmojiPicker({
        emojiable_selector: '[data-emojiable=true]',
        assetsPath: '/static/lib/emoji-picker/img',
        popupButtonClasses: 'icon hand peace'
      });
    // Finds all elements with `emojiable_selector` and converts them to rich emoji input fields
    // You may want to delay this step if you have dynamically created input fields that appear later in the loading process
    // It can be called as many times as necessary; previously converted input fields will not be converted again
    emojiPicker.discover();

    // angular.element('#newTweetMessageArea .emoji-wysiwyg-editor').focus();
  }


  $scope.toggleRefreshButton = function() {
    $route.reload();
  }

  $scope.triggerLogout = function() {
    $http({
      method: 'PUT',
      url: apiBaseUrl+"/user/logout",
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      console.log(response.data);
      $window.location.reload();
    }, function errorCallback(response) {
      console.log("fuxked");
    });
  }
});






myApp.controller('newTweetModalCntlr', function($scope, $http, $rootScope){
  console.log("newTweetModalCntlr started");

  var selectedFont = "";

  angular.element('#newTweetForm').submit(false);

  angular.element('#newTweetErrorModal').modal({
    onHidden: function() {
      angular.element('#newTweetModal').modal('show');
    }
  });


  $scope.newTweet = {};
  $scope.newTweetErrorMessage = "";

  $scope.uploadFile = function(event){
    var file = event.target.files[0];
    $scope.newTweet.file = file;
    if (allowedMimetype.indexOf(file.type) == -1) {
      console.log("makeNewTweet error: invalid mime type");
      $scope.newTweetErrorMessage = "Our system only support .jpg or .png image file";
      angular.element('#newTweetErrorModal').modal('show');
      return false;
    }
  };


  $scope.makeNewTweet = function() {
    var message = angular.element("#newTweetTextArea").val();
    // var imageFile = angular.element('#newTweetFile')[0].files[0];
    var imageFile = $scope.newTweet.file;
    var formData = new FormData();

    var haveImage = false;
    if (typeof imageFile != 'undefined' && imageFile != null) {
      if (allowedMimetype.indexOf(imageFile.type) == -1) {
        console.log("makeNewTweet error: invalid mime type");
        $scope.newTweetErrorMessage = "Our system only support .jpg or .png image file";
        angular.element('#newTweetErrorModal').modal('show');
        console.log("mime type fuxked");
        return false;
      } else {
        formData.append('image', imageFile);
        haveImage = true;
      }
    } else {
      // it is fine if we dont have an image
    }

    if (typeof message != 'undefined' && message.length > maxNewTweetMessageCharacters) {
      $scope.newTweetErrorMessage = "Your message is too long.";
      console.log('mnessage too long');
      angular.element('#newTweetErrorModal').modal('show');
      return false;
    }

    var selectedColor = angular.element('#colorSelectionDropdown').dropdown('get value');
    // console.log("color: "+selectedColor);
    formData.append('color',selectedColor);

    if (typeof message != 'undefined' && message != "") {
      formData.append('message',message);
      formData.append('font',selectedFont);
    } else if (haveImage) {
      formData.append('message','');
      formData.append('font','');
    } else {
      console.log("makeNewTweet error: cant post emtpy message");
      angular.element('#newTweetForm').addClass('error');
      return false;
    }

    angular.element('#newTweetForm').removeClass('error');


    console.log('posting new message');
    angular.element('#newTweetForm').addClass('loading');
    $http({
      method: 'POST',
      url: apiBaseUrl+"/tweets/post",
      data: formData,
      headers: {'Content-Type': undefined},
      transformRequest: angular.identity,
      // angular.identity prevents angular to do anything on our data, like serializing it
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      // console.log($scope.profile);
      angular.element('#newTweetForm').removeClass('loading');
      angular.element('#newTweetModal').modal('hide');
      angular.element('#newTweetForm').form('clear');
      $scope.clearNewTweetForm();

      $rootScope.$broadcast('newTweetPostEvent', {message:'kelvin'});

    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.
      console.log(response.data);
      angular.element('#newTweetErrorModal').modal('show');
      angular.element('#newTweetForm').removeClass('loading');
    });
  }




  // from Google webfont
  $scope.googleFonts = fontList;
  setTimeout(function() {
    angular.element('#fontSelectionDropdown').dropdown();
  },2000);


  $scope.selectNewTweetFont = function(font) {
    document.getElementById('newTweetMessageArea').style.fontFamily = font;
    selectedFont = font;
  }

  $scope.clearNewTweetForm = function() {
    angular.element('#newTweetTextArea').val("");
    angular.element('.emoji-wysiwyg-editor').html("");
    angular.element('#fontSelectionDropdown').dropdown('restore defaults');
    angular.element('#colorSelectionDropdown').dropdown('restore defaults');
    angular.element('#newTweetFile').val(null);
    delete $scope.newTweet.file;
  }


  $scope.maxNewTweetMessageCharacters = maxNewTweetMessageCharacters;

  angular.element('.charCounterDisplay').html('Characters remain: 0/'+maxNewTweetMessageCharacters);

  $scope.charCounterAreaKeyup = function($event) {
    var content = angular.element(".emoji-wysiwyg-editor").html();
    var newLineCount = (content.match(/\<div\>/g) || []).length;
    content = content.replace(/\<div\>/g,' ');
    content = content.replace(/\<br\>/g,'');
    content = content.replace(/\<\/div\>/g,'');
    var length = content.length - newLineCount;
    angular.element('.charCounterDisplay').html('Characters remain: '+length+'/'+maxNewTweetMessageCharacters);
  }


  // get all the available mood from backend
  $http({
    method: 'GET',
    url: '/static/data/moods.json',
    timeout: TIMEOUT_LIMIT
  }).then(function successCallback(response) {
    // console.log(response);
    $scope.availableMoods = response.data;
    availableMoods = response.data;
    // setup the dropdown for color selection
    angular.element('#colorSelectionDropdown').dropdown();
  }, function errorCallback(response) {
    console.log('unable to get all moods for new tweets');
    console.log(response.data);
  });
});






// controller of the view
myApp.controller('profileCntlr',function($scope, $route, $http, $interval, $location, $window) {
  console.log('profileCntlr started');

  var params = $route.current.params;
  var userId = params.userId;

  $scope.allTweetsBusyLoadingData = false;

  pollUserProfile();
  pollUserTweets();

  // get all the tweets of this user in the profile
  $interval(function() {
    if ($route.current.$$route.controller == 'profileCntlr' && !isCurrentProfileMyProfile()) {
      pollUserProfile();
    }
  }, POLLING_INTERVAL);





  $scope.triggerFollowButton = function() {
    var targetUserId = $scope.profile.id;
    // console.log("following");
    setFollowButtonLoading();

    $http({
      method: 'PUT',
      url: apiBaseUrl+"/follow/"+targetUserId,
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      // console.log(response.data.following);
      $scope.myProfile.following = response.data.following;
      resetFollowButtonLoading();
    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.

      console.log("Fail to follow");
      resetFollowButtonLoading();
    });
  }

  $scope.triggerUnfollowButton = function() {
    var targetUserId = $scope.profile.id;
    // console.log("unfollowing");
    setFollowButtonLoading();
    $http({
      method: 'PUT',
      url: apiBaseUrl+"/unfollow/"+targetUserId,
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      // console.log(response.data.following);
      $scope.myProfile.following = response.data.following;
      resetFollowButtonLoading();
    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.
      console.log("Fail to unfollow");
      resetFollowButtonLoading();
    });
  }


  function pollUserProfile() {
    // pull the profile for this user
    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/"+userId+"/profile",
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      $scope.profile = response.data;
      // console.log($scope.profile);
    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.

      console.log("Fail to retrive current user profile");
      $location.path('/error').replace();
      $scope.$apply();
    });
  }





  function isCurrentProfileMyProfile() {
    return userId == $scope.myProfile.id;
  }


  function pollUserTweets() {
    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/"+userId+"/tweets",
      params: {
        'limit': POLL_TWEETS_LIMIT,
      },
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      $scope.tweets = response.data.tweets;
      if ($scope.tweets.length > 0) {
        setTimeout(function() {
          allTweetsHeightCheck();
        },1000);
      }

      // console.log($scope.tweets);

      setTimeout(function() {
        initProfileSticky();
      },100);
      // console.log($scope.profile);
    }, function errorCallback(response) {
      // called asynchronously if an error occurs
      // or server returns response with an error status.
      console.log("Fail pull user tweets");

      $location.path('/error').replace();
      $scope.$apply();

    });
  }

  function allTweetsHeightCheck() {
    var limit = 2;
    while (angular.element('#allTweets').height() < $window.innerHeight) {
      // console.log(angular.element('#allTweets').height() +" / "+ $window.innerHeight);
      loadMoreTweets();
      if (limit == 0)
        break;
      limit--;
    }
  }

  $scope.loadMoreTweets = loadMoreTweets;

  function loadMoreTweets() {
    var tweets = $scope.tweets;
    if(tweets === undefined || tweets.length <= 0 || $scope.allTweetsBusyLoadingData)
      return;
    $scope.allTweetsBusyLoadingData = true;
    angular.element('#userProfileTweetsLoadingIndicator').addClass('active');
    var lastTweetId = tweets[tweets.length-1].tweet_id

    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/"+userId+"/tweets",
      params: {
        'limit': POLL_TWEETS_LIMIT,
        'from_tweet_id': lastTweetId,
      },
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {

      if (response.data.count >= POLL_TWEETS_LIMIT){
        $scope.allTweetsBusyLoadingData = false;
      }
      $scope.tweets = $scope.tweets.concat(response.data.tweets);
      angular.element('#userProfileTweetsLoadingIndicator').removeClass('active');

      setTimeout(function() {
        initProfileSticky();
      },100);
      // console.log($scope.profile);
    }, function errorCallback(response) {
      angular.element('#userProfileTweetsLoadingIndicator').removeClass('active');
      console.log("Fail pull user tweets");
      $location.path('/error').replace();
      $scope.$apply();
    });
  }


  function initProfileSticky() {
    if (angular.element('#stickyUserProfile').height() < angular.element('#allTweets').height()) {
      angular.element('#stickyUserProfile')
        .sticky({
          context: '#allTweets',
          offset: 55,
          jitter: 5,
          pushing: true,
          observeChanges: true,
        });
    }
  }

  function setFollowButtonLoading() {
    var btn = angular.element("#userProfileFollowButton");
    btn.addClass('loading');
  }

  function resetFollowButtonLoading() {
    var btn = angular.element("#userProfileFollowButton");
    btn.removeClass('loading');
  }


  // Following
  $scope.triggerFollowingModal = function() {
    $scope.following = null;
    $scope.followingLoaderMessage = "Loading";

    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/"+userId+"/following",
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      $scope.following = response.data.results;
      // console.log(response.data.results);
      // console.log($scope.profile);
    }, function errorCallback(response) {
      $scope.followingLoaderMessage = "Unable to get following";

      console.log('Unable to poll list of following for user: '+userId);
    });
    angular.element('#followingModal').modal('show');
  }

  $scope.selectFollowingUser = function(userId) {
    angular.element('.modal').modal('hide');
    $location.path('/user/'+userId+'/profile').replace();
    apply();
  }


  // Followers
  $scope.triggerFollowersModal = function() {
    $scope.followers = null;
    $scope.followersLoaderMessage = "Loading";
    angular.element('#followersModal').modal('show');

    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/"+userId+"/followers",
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      $scope.followers = response.data.results;
      // console.log(response.data.results);
      // console.log($scope.profile);
    }, function errorCallback(response) {
      $scope.followersLoaderMessage = "Unable to get followers";
      console.log('Unable to poll list of following for user: '+userId);
    });
  }

  $scope.selectFollower = function(userId) {
    angular.element('.modal').modal('hide');
    $location.path('/user/'+userId+'/profile').replace();
  }

  $scope.triggerDeleteTweet = function(tweetId) {
    angular.element('#deleteConfirmationModal')
      .modal({
        closable: false,
        blurring: true,
        onApprove: function() {
          deleteTweet(tweetId);
        }
      })
      .modal('show');

  }

  function deleteTweet(tweetId) {
    angular.element("#tweetPostLoader_"+tweetId).addClass('active');

    $http({
      method: 'DELETE',
      url: apiBaseUrl+"/tweets/"+tweetId,
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // console.log(response.data);
      pollUserTweets();
    }, function errorCallback(response) {
      console.log("Unable to delete tweet: "+tweetId);
    });
    angular.element("#tweetPostLoader."+tweetId).removeClass('active');
  }


  $scope.triggerLikeTweet = function(tweetId, isLike) {
    // console.log(tweetId);
    // console.log(isLike);

    if (isLike) {
      $http({
        method: 'PUT',
        url: apiBaseUrl+"/tweets/"+tweetId+"/like",
        timeout: TIMEOUT_LIMIT
      }).then(function successCallback(response) {
        var entry = $scope.tweets.find(function(json) {
          return json['tweet_id'] == response.data.tweet_id;
        });
        entry.likes = response.data.likes;
      }, function errorCallback(response) {
        console.log("unable to like the tweet")
      });
    } else {
      $http({
        method: 'PUT',
        url: apiBaseUrl+"/tweets/"+tweetId+"/unlike",
        timeout: TIMEOUT_LIMIT
      }).then(function successCallback(response) {
        var entry = $scope.tweets.find(function(json) {
          return json['tweet_id'] == response.data.tweet_id;
        });
        entry.likes = response.data.likes;

        // console.log($scope.profile);
      }, function errorCallback(response) {
        console.log("unable to unlike the tweet")
      });
    }
  }


  // listen to the new tweet event
  // get the user profile and reload the tweets if the profile is for the current user.
  $scope.$on('newTweetPostEvent', function(event, data) {
    if ($route.current.$$route.controller == 'profileCntlr' && isCurrentProfileMyProfile()) {
      pollUserProfile();
      pollUserTweets();
    }
  });

});



// not using at the moment
myApp.controller('tweetPostAnimatinCntlr', function($scope) {
  $scope.addRaiseClass = function($event) {
    var elem = $(event.currentTarget);
    elem.addClass('raised');
    console.log('raised');
  }

  $scope.removeRaiseClass = function() {
    var elem = $(event.currentTarget);
    elem.removeClass('raised');
  }
});













myApp.controller('newsFeedCntlr', function($scope, $http, $location, $route, $window) {
  console.log("newsFeedCntlr started");

  $scope.tweetsBusyLoadingData = false;
  angular.element('#newsFeedTweetsLoadingIndicator').addClass('active');
  $http({
    method: 'GET',
    url: apiBaseUrl+"/tweets/following",
    params: {
      'limit': POLL_TWEETS_LIMIT,
    },
    timeout: TIMEOUT_LIMIT
  }).then(function successCallback(response) {
    // this callback will be called asynchronously
    // when the response is available
    $scope.tweets = response.data;
    if ($scope.tweets.length > 0) {
      setTimeout(function() {
        allTweetsHeightCheck();
      },1000);
    }

    angular.element('#newsFeedTweetsLoadingIndicator').removeClass('active');
  }, function errorCallback(response) {
    // called asynchronously if an error occurs
    // or server returns response with an error status.
    console.log("Fail pull new feeds");
    angular.element('#newsFeedTweetsLoadingIndicator').removeClass('active');
  });
  

  $scope.triggerLikeTweet = function(tweetId, isLike) {
    // console.log(tweetId);
    // console.log(isLike);

    if (isLike) {
      $http({
        method: 'PUT',
        url: apiBaseUrl+"/tweets/"+tweetId+"/like",
        timeout: TIMEOUT_LIMIT
      }).then(function successCallback(response) {
        var entry = $scope.tweets.find(function(json) {
          return json['tweet_id'] == response.data.tweet_id;
        });
        entry.likes = response.data.likes;
      }, function errorCallback(response) {
        console.log("unable to like the tweet")
      });
    } else {
      $http({
        method: 'PUT',
        url: apiBaseUrl+"/tweets/"+tweetId+"/unlike",
        timeout: TIMEOUT_LIMIT
      }).then(function successCallback(response) {
        var entry = $scope.tweets.find(function(json) {
          return json['tweet_id'] == response.data.tweet_id;
        });
        entry.likes = response.data.likes;

        // console.log($scope.profile);
      }, function errorCallback(response) {
        console.log("unable to unlike the tweet")
      });
    }
  }

  function allTweetsHeightCheck() {
    var limit = 2;
    while (angular.element('#newsFeedPageTweetsInfiniteScroll').height() < $window.innerHeight) {
      // console.log(angular.element('#newsFeedPageTweetsInfiniteScroll').height() +" / "+ $window.innerHeight);
      $scope.loadMoreTweets();
      if (limit == 0)
        break;
      limit--;
    }
  }

  $scope.loadMoreTweets = function () {
    var tweets = $scope.tweets;
    if(tweets === undefined || $scope.tweetsBusyLoadingData || tweets.length <= 0)
      return;

    $scope.tweetsBusyLoadingData = true;
    angular.element('#newsFeedTweetsLoadingIndicator').addClass('active');
    var lastTweetId = tweets[tweets.length-1].tweet_id
    // console.log('load more');
    $http({
      method: 'GET',
      url: apiBaseUrl+"/tweets/following",
      params: {
        'limit': POLL_TWEETS_LIMIT,
        'from_tweet_id': lastTweetId,
      },
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {

      if (response.data.length >= POLL_TWEETS_LIMIT){
        $scope.tweetsBusyLoadingData = false;
      }
      $scope.tweets = $scope.tweets.concat(response.data);
      angular.element('#newsFeedTweetsLoadingIndicator').removeClass('active');

    }, function errorCallback(response) {
      angular.element('#newsFeedTweetsLoadingIndicator').removeClass('active');
      console.log("Fail pull user tweets");
    });
  }

});












myApp.controller('loginCntlr',function($scope, $route, $http, $interval, $location) {
  console.log("loginCntlr started");


});






myApp.controller('appCntlr', function($scope, $http, $location, $interval) {
  console.log("appCntlr started");
  $scope.isLogin = false;
  $scope.apiBaseUrl = apiBaseUrl;


  pullMyProfile();
  $interval(function() {
    if ($scope.isLogin) {
      pullMyProfile();
    }
  }, POLLING_INTERVAL);



  // pull the profile for this user
  function pullMyProfile() {
    $http({
      method: 'GET',
      url: apiBaseUrl+"/user/profile",
      timeout: TIMEOUT_LIMIT
    }).then(function successCallback(response) {
      // this callback will be called asynchronously
      // when the response is available
      $scope.isLogin = true;
      angular.element('#signinModal').modal('hide');
      $scope.myProfile = response.data;

      console.log('myProfile udpated !!!');
      // console.log($scope.profile);
    }, function errorCallback(response) {
      angular.element('#signinModal')
      .modal({
        closable: false,
      })
      .modal('show');
      // called asynchronously if an error occurs
      // or server returns response with an error status.

      console.log("Fail to retrive current user profile, redirecting to login page");
    });
  }

  $scope.triggerLoginBtn = function() {
    $scope.isLoggingIn = true;
  }


  $scope.getMoodDescription = function(color) {
    if (availableMoods != null) {
      for (var i in availableMoods) {
        var mood = availableMoods[i];
        if (mood['color'] == color) {
          return mood['description'].toLowerCase();
        }
      }
      return 'okay';
    } else {
      return 'okay';
    }
  }

});


















myApp.directive('customOnChange', function() {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      var onChangeHandler = scope.$eval(attrs.customOnChange);
      element.bind('change', onChangeHandler);
    }
  };
});




// https://scotch.io/tutorials/single-page-apps-with-angularjs-routing-and-templating

myApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: '/static/partials/news-feed.html',
        controller: 'newsFeedCntlr'
      }).
      when('/user/:userId/profile', {
        templateUrl: '/static/partials/user-profile.html',
        controller: 'profileCntlr'
      }).
      when('/user/info', {
        templateUrl: '/static/partials/user-info.html',
      }).
      otherwise({
        redirectTo: '/'
      });
  }
]);
