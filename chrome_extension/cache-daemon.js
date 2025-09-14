self.addEventListener('install', () => {
  console.log('Cache daemon installed');
});

self.addEventListener('activate', () => {
  console.log('Cache daemon activated');
});

self.addEventListener('message', event => {
  console.log('Cache daemon received message', event.data);
});
