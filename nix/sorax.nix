{
  lib,
  stdenvNoCC,
  callPackage,
  bun,
  nodejs,
  sysctl,
  makeBinaryWrapper,
  models-dev,
  ripgrep,
  wayland,
  installShellFiles,
  versionCheckHook,
  writableTmpDirAsHomeHook,
  node_modules ? callPackage ./node_modules.nix { },
}:
stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "sorax";
  inherit (node_modules) version src;
  inherit node_modules;

  nativeBuildInputs = [
    bun
    nodejs # for patchShebangs node_modules
    installShellFiles
    makeBinaryWrapper
    models-dev
    writableTmpDirAsHomeHook
  ];

  postPatch = ''
    # NOTE: Relax Bun version check to be a warning instead of an error
    substituteInPlace packages/script/src/index.ts \
      --replace-fail 'throw new Error(`This script requires bun@''${expectedBunVersionRange}' \
                     'console.warn(`Warning: This script requires bun@''${expectedBunVersionRange}'
  '';

  configurePhase = ''
    runHook preConfigure

    cp -R ${finalAttrs.node_modules}/. .
    patchShebangs node_modules
    patchShebangs packages/*/node_modules

    runHook postConfigure
  '';

  env.MODELS_DEV_API_JSON = "${models-dev}/dist/_api.json";
  env.SORAX_DISABLE_MODELS_FETCH = true;
  env.SORAX_VERSION = finalAttrs.version;
  env.SORAX_CHANNEL = "prod";
  env.NODE_OPTIONS = "--max-old-space-size=4096";

  buildPhase = ''
    runHook preBuild

    cd ./packages/cli
    bun --bun ./script/build.ts --single --skip-install

    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    install -Dm755 dist/cli-*/bin/sorax $out/bin/sorax

    # OpenTUI dlopens Wayland for clipboard images.
    wrapProgram $out/bin/sorax \
      --prefix PATH : ${
        lib.makeBinPath (
          [
            ripgrep
          ]
          # bun runs sysctl to detect if running on rosetta2
          ++ lib.optional stdenvNoCC.hostPlatform.isDarwin sysctl
        )
      } ${lib.optionalString stdenvNoCC.hostPlatform.isLinux ''
        --prefix LD_LIBRARY_PATH : ${lib.makeLibraryPath [ wayland ]}
      ''}

    ln -s sorax $out/bin/sorax2

    runHook postInstall
  '';

  postInstall = lib.optionalString (stdenvNoCC.buildPlatform.canExecute stdenvNoCC.hostPlatform) ''
    # v2 dropped the `completion` subcommand; --completions is the global flag.
    # --completions also accepts sh, which emits the same script as bash.
    # staged to files, substitute below rejects anything that is not a regular file
    $out/bin/sorax --completions bash > sorax.bash
    $out/bin/sorax --completions zsh > _sorax
    $out/bin/sorax --completions fish > sorax.fish

    installShellCompletion --cmd sorax \
      --bash sorax.bash \
      --fish sorax.fish \
      --zsh _sorax

    # SORAX_CLI_NAME is a build-time define, so the sorax2 copies are
    # renamed rather than regenerated. --replace-fail is a global literal
    # substitution, so any lowercase sorax that later appears in a
    # description or help text ships as sorax2 in the sorax2 copy.
    substitute sorax.bash sorax2.bash --replace-fail sorax sorax2
    substitute _sorax _sorax2 --replace-fail sorax sorax2
    substitute sorax.fish sorax2.fish --replace-fail sorax sorax2

    installShellCompletion --cmd sorax2 \
      --bash sorax2.bash \
      --fish sorax2.fish \
      --zsh _sorax2
  '';

  nativeInstallCheckInputs = [
    versionCheckHook
    writableTmpDirAsHomeHook
  ];
  doInstallCheck = true;
  versionCheckKeepEnvironment = [ "HOME" "SORAX_DISABLE_MODELS_FETCH" ];
  versionCheckProgramArg = "--version";

  passthru = {
    env = finalAttrs.env;
  };

  meta = {
    description = "The open source coding agent";
    homepage = "https://sorax.ai";
    license = lib.licenses.mit;
    mainProgram = "sorax";
    inherit (node_modules.meta) platforms;
  };
})
