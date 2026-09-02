declare module '@barba/core' {
  const barba: {
    init: (config?: any) => void;
    destroy: () => void;
    use: (plugin: any) => void;
  };
  export default barba;
}
