export default [
  {
    path: '/login',
    component: '@/pages/Login',
  },
  {
    path: '/',
    component: '@/layouts/BasicLayout',
    routes: [
      { path: '/', redirect: '/dashboard' },
      { path: '/dashboard', component: '@/pages/Dashboard', title: '数据看板' },
      {
        path: '/members',
        title: '会员管理',
        routes: [
          { path: '/members', component: '@/pages/members/List', title: '会员列表' },
          { path: '/members/create', component: '@/pages/members/Create', title: '新增会员' },
          { path: '/members/:id', component: '@/pages/members/Detail', title: '会员详情' },
        ],
      },
      {
        path: '/courses',
        title: '课程管理',
        routes: [
          { path: '/courses', component: '@/pages/courses/List', title: '课程列表' },
          { path: '/courses/create', component: '@/pages/courses/Create', title: '新增课程' },
          { path: '/courses/schedules', component: '@/pages/courses/Schedules', title: '排课管理' },
        ],
      },
      {
        path: '/bookings',
        title: '预约管理',
        routes: [
          { path: '/bookings', component: '@/pages/bookings/List', title: '预约列表' },
          { path: '/bookings/checkin', component: '@/pages/bookings/Checkin', title: '签到管理' },
        ],
      },
      {
        path: '/coaches',
        title: '教练管理',
        routes: [
          { path: '/coaches', component: '@/pages/coaches/List', title: '教练列表' },
          { path: '/coaches/create', component: '@/pages/coaches/Create', title: '新增教练' },
        ],
      },
      {
        path: '/finance',
        title: '财务管理',
        routes: [
          { path: '/finance/orders', component: '@/pages/finance/Orders', title: '订单管理' },
          { path: '/finance/reports', component: '@/pages/finance/Reports', title: '财务报表' },
        ],
      },
      {
        path: '/system',
        title: '系统设置',
        routes: [
          { path: '/system/users', component: '@/pages/system/Users', title: '用户管理' },
          { path: '/system/roles', component: '@/pages/system/Roles', title: '角色管理' },
          { path: '/system/settings', component: '@/pages/system/Settings', title: '系统配置' },
        ],
      },
    ],
  },
];