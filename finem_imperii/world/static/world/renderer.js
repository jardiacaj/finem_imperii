function MapRenderer(region_raw_data, focus_region_id) {

    var zis = this;

    /* API */

    this.region_callback = undefined;
    this.settlement_callback = undefined;
    this.click_callback = undefined;

    this.highlight_settlement = function (settlement_id) {
        for (var i = 0; i < region_raw_data.length; i++) {
            var region = region_raw_data[i];
            for (var j = 0; j < region.settlements.length; j++) {
                var settlement = region.settlements[j];
                if (settlement.id == settlement_id) {
                    settlement.mesh.material = zis.settlement_material_highlighted;
                    zis.render();
                }
            }
        }
    };

    this.enable_region_tags = function () {

    };

    /* INTERNALS */

    zis.init_camera = function () {
        zis.camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        zis.camera.position.z = 2.5;
        zis.camera.position.x = 2.5;
        zis.camera.position.y = 12;
        zis.camera.lookAt(new THREE.Vector3( 0, 0, 0 ));
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
    };

    zis.init_renderer = function () {
        zis.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        zis.renderer.setSize(window.innerWidth, window.innerHeight);
        zis.renderer.setClearColor( 0xffffff, 0);
    };

    zis.add_orbit_controls = function () {
        zis.controls = new THREE.OrbitControls(zis.camera, zis.renderer.domElement);
        zis.controls.addEventListener( 'change', zis.render );
    };

    zis.init_lighting = function () {
        zis.ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
        zis.scene.add(zis.ambientLight);
        zis.directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        zis.directionalLight.position.set(1, 1, 1).normalize();
        zis.scene.add(zis.directionalLight);
    };

    zis.render_region_REFACTOR_ME = function () {
        var mesh = new THREE.Mesh(zis.region_geometry, zis.region_materials[region.type]);
        var geo = new THREE.EdgesGeometry( mesh.geometry );
        var mat = new THREE.LineBasicMaterial( { color: 0x000000, linewidth: 1 } );
        var wireframe = new THREE.LineSegments( geo, mat );
        mesh.add( wireframe );

        mesh.position.x = region.x_pos - 1;
        mesh.position.z = region.z_pos - 1;
        mesh.position.y = region.y_pos;

        region_raw_data[i].mesh = mesh;
        mesh.region = region_raw_data[i];

        zis.scene.add(mesh);

        if (focus_region_id == region.id) {
            zis.camera.position.x = mesh.position.x;
            zis.camera.position.y = 4;
            zis.camera.position.z = mesh.position.z;
            zis.camera.lookAt(mesh.position);
        }

        if (false) { // show_region_tags) {
            zis.camera.updateMatrixWorld();
            zis.camera.updateProjectionMatrix();

            var width = window.innerWidth, height = window.innerHeight;
            var widthHalf = width / 2, heightHalf = height / 2;

            var pos = mesh.position.clone();
            pos.y += 0.5;
            pos.project(zis.camera);
            pos.x = ( pos.x * widthHalf ) + widthHalf;
            pos.y = -( pos.y * heightHalf ) + heightHalf;

            if (pos.x < width && pos.y < height) {
                var region_tag = document.createElement('div');
                region_tag.style.position = 'absolute';
                region_tag.style.width = "100px";
                region_tag.style.textAlign = "center";
                region_tag.style.height = 100;
                region_tag.style.background = "transparent";
                region_tag.innerHTML = region.name;
                region_tag.style.top = pos.y + 'px';
                region_tag.style.left = (pos.x - 50) + 'px';
                document.body.appendChild(region_tag);
            }
        }

        for (var j = 0; j < region.settlements.length; j++) {
            var settlement = region.settlements[j];

            var radius = Math.log10(settlement.population) * 0.02;
            var settlement_geometry = new THREE.CylinderGeometry( radius, radius, 0.01, 16 );
            var cylinder = new THREE.Mesh( settlement_geometry, zis.settlement_material );
            cylinder.position.x = (region.x_pos - 1) - 0.5 + settlement.x_pos/100;
            cylinder.position.z = (region.z_pos - 1) - 0.5 + settlement.z_pos/100;
            cylinder.position.y = region.y_pos + 0.5;

            cylinder.settlement = settlement;
            region_raw_data[i].settlements[j].mesh = cylinder;

            zis.scene.add(cylinder);
        }
    };

    zis.mouse_move_listener = function (event) {
        // it's pointless to do anything if there are no callbacks set
        if(zis.region_callback === undefined && zis.settlement_callback === undefined && zis.click_callback === undefined)
            return;
        // calculate mouse position in normalized device coordinates
        // (-1 to +1) for both components
        zis.mouse_vector.x = (event.clientX / window.innerWidth ) * 2 - 1;
        zis.mouse_vector.y = - (event.clientY / window.innerHeight) * 2 + 1;
        zis.pick();
    };

    zis.window_resize_listener = function (event) {
        zis.camera.aspect = window.innerWidth / window.innerHeight;
        zis.camera.updateProjectionMatrix();
        zis.renderer.setSize( window.innerWidth, window.innerHeight );
        zis.render();
        zis.pick();
    };

    zis.mouse_click_listener_notifier = function (event) {
        if (zis.click_callback !== undefined) {
            return zis.click_callback(zis.picked_region, zis.picked_settlement);
        }
    };

    zis.notify_region_pick = function (region) {
        if (region !== zis.picked_region) {
            zis.picked_region = region;
            if (zis.region_callback !== undefined) return zis.region_callback(region);
        }
    };

    zis.notify_settlement_pick = function (settlement) {
        if (settlement !== zis.picked_settlement) {
            zis.picked_settlement = settlement;
            if (zis.settlement_callback !== undefined) return zis.settlement_callback(settlement);
        }
    };

    zis.pick = function () {
        zis.raycaster.setFromCamera( zis.mouse_vector, zis.camera );

        // calculate objects intersecting the picking ray
        var intersects = zis.raycaster.intersectObjects( zis.scene.children );
        var region_intersected = false;
        var settlement_intersected = false;

        // notify only the first intersected element
        for ( var i = 0; i < intersects.length; i++ ) {

            var region = intersects[ i ].object.region;
            if (region !== undefined && !region_intersected) {
                zis.notify_region_pick(region);
                region_intersected = true;
            }
            var settlement = intersects[ i ].object.settlement;
            if (settlement !== undefined && !settlement_intersected) {
                zis.notify_settlement_pick(settlement);
                settlement_intersected = true;
            }

        }

        if (!settlement_intersected) zis.notify_settlement_pick(undefined);
        if (!region_intersected) zis.notify_region_pick(undefined);
    };

    zis.render = function () {
        zis.renderer.render(zis.scene, zis.camera);
    };


    zis.region_geometry = new THREE.CubeGeometry(1, 1, 1);
    zis.region_materials = {
        "plains": new THREE.MeshLambertMaterial({color: 0x90CD00, shading: THREE.SmoothShading}),
        "forest": new THREE.MeshLambertMaterial({color: 0x207F07, shading: THREE.SmoothShading}),
        "shore": new THREE.MeshLambertMaterial({color: 0x0D81CD, shading: THREE.SmoothShading}),
        "deepsea": new THREE.MeshLambertMaterial({color: 0x000E85, shading: THREE.SmoothShading}),
        "mountain": new THREE.MeshLambertMaterial({color: 0x837D71, shading: THREE.SmoothShading}),
    };
    zis.settlement_material_highlighted = new THREE.MeshBasicMaterial( {color: 0xFFFFFF} );
    zis.settlement_material = new THREE.MeshBasicMaterial( {color: 0x000000} );

    zis.picked_region = undefined;
    zis.picked_settlement = undefined;


    zis.canvas_container = document.createElement( 'div' );
    document.body.appendChild( zis.canvas_container );

    zis.scene = new THREE.Scene();
    zis.init_camera();
    zis.init_renderer();
    zis.init_lighting();
    zis.raycaster = new THREE.Raycaster();
    zis.mouse_vector = new THREE.Vector2();

    zis.canvas_container.appendChild(zis.renderer.domElement);

    $(window).on('resize', zis.window_resize_listener);
    $(document).on('mousemove', zis.mouse_move_listener);
    $(document).on('click', zis.mouse_click_listener_notifier);

    for (var i = 0; i < region_raw_data.length; i++)  {
        var region = region_raw_data[i];
        zis.render_region_REFACTOR_ME(region);
    }

    zis.render();

}