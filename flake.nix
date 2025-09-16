{
  description = "AanvraagApp";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/25.05";

    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, nixpkgs-unstable, ... }: let
    pkgs = nixpkgs.legacyPackages."x86_64-linux";
    pkgs-unstable = nixpkgs-unstable.legacyPackages."x86_64-linux";
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      packages = [
        pkgs.python313
        pkgs.poetry
        pkgs.rustc # For pydantic-core
        pkgs.cargo # For pydantic-core
        pkgs.fish
      ];

      env = {
         LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
            pkgs.zlib
            pkgs.rustc
            pkgs.cargo
         ];
      };

      shellHook = ''
         echo "You are now using a NIX environment"
         export SHELL="${pkgs.fish}/bin/fish"
      '';
    };
  };
}
