export default defineAppConfig({
  pages: [
    'pages/index/index',
    'pages/login/index',
    'pages/courses/index',
    'pages/booking/index',
    'pages/profile/index',
    'pages/checkin/index',
    'pages/profile/body-test/index',
    'pages/profile/orders/index',
    'pages/profile/settings/index',
  ],
  window: {
    backgroundTextStyle: 'light',
    navigationBackgroundColor: '#1a1a2e',
    navigationBarTitleText: 'FitAI',
    navigationBarTextStyle: 'white',
    navigationStyle: 'custom',
  },
  tabBar: {
    color: '#999999',
    selectedColor: '#7c5cfc',
    backgroundColor: '#ffffff',
    borderStyle: 'black',
    list: [
      {
        pagePath: 'pages/index/index',
        text: '首页',
        iconPath: 'assets/tab-home.png',
        selectedIconPath: 'assets/tab-home-active.png',
      },
      {
        pagePath: 'pages/courses/index',
        text: '课程',
        iconPath: 'assets/tab-course.png',
        selectedIconPath: 'assets/tab-course-active.png',
      },
      {
        pagePath: 'pages/booking/index',
        text: '预约',
        iconPath: 'assets/tab-booking.png',
        selectedIconPath: 'assets/tab-booking-active.png',
      },
      {
        pagePath: 'pages/profile/index',
        text: '我的',
        iconPath: 'assets/tab-profile.png',
        selectedIconPath: 'assets/tab-profile-active.png',
      },
    ],
  },
})
