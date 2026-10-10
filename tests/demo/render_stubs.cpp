#include "I:/CodeX Project/KG3D_Cloth/FleX/demo/shaders.h"
void GetRenderDevice(void** device, void** context) {}
void InitRender(const RenderInitOptions& options) {}
void DestroyRender() {}
void ReshapeRender(SDL_Window* window) {}
void StartFrame(Vec4 clearColor) {}
void EndFrame() {}
void StartGpuWork() {}
void EndGpuWork() {}
void FlushGraphicsAndWait() {}
void PresentFrame(bool fullsync) {}
void GetViewRay(int x, int y, Vec3& origin, Vec3& dir) {}
void ReadFrame(int* backbuffer, int width, int height) {}
void SetView(Matrix44 view, Matrix44 proj) {}
void SetFillMode(bool wireframe) {}
void SetCullMode(bool enabled) {}
void BeginLines() {}
void DrawLine(const Vec3& p, const Vec3& q, const Vec4& color) {}
void EndLines() {}
ShadowMap* ShadowCreate() {return {};}
void ShadowDestroy(ShadowMap* map) {}
void ShadowBegin(ShadowMap* map) {}
void ShadowEnd() {}
RenderTexture* CreateRenderTexture(const char* filename) {return {};}
RenderTexture* CreateRenderTarget(int with, int height, bool depth) {return {};}
void DestroyRenderTexture(RenderTexture* tex) {}
void SetRenderTarget(RenderTexture* target) {}
RenderMesh* CreateRenderMesh(const Mesh* m) {return {};}
void DestroyRenderMesh(RenderMesh* m) {}
void DrawRenderMesh(RenderMesh* m, const Matrix44& xform, const RenderMaterial& mat) {}
void DrawRenderMeshInstances(RenderMesh* m, const Matrix44* xforms, int n, const RenderMaterial& mat) {}
void DrawPlanes(Vec4* planes, int n, float bias) {}
void DrawPoints(FluidRenderBuffers* buffer, int n, int offset, float radius, float screenWidth, float screenAspect, float fov, Vec3 lightPos, Vec3 lightTarget, Matrix44 lightTransform, ShadowMap* shadowTex, bool showDensity) {}
void DrawMesh(const Mesh*, Vec3 color) {}
void DrawCloth(const Vec4* positions, const Vec4* normals, const float* uvs, const int* indices, int numTris, int numPositions, int colorIndex, float expand, bool twosided, bool smooth) {}
void DrawBuffer(float* buffer, Vec3 camPos, Vec3 lightPos) {}
void DrawRope(Vec4* positions, int* indices, int numIndices, float radius, int color) {}
GpuMesh* CreateGpuMesh(const Mesh* m) {return {};}
void DestroyGpuMesh(GpuMesh* m) {}
void DrawGpuMesh(GpuMesh* m, const Matrix44& xform, const Vec3& color) {}
void DrawGpuMeshInstances(GpuMesh* m, const Matrix44* xforms, int n, const Vec3& color) {}
void BindSolidShader(Vec3 lightPos, Vec3 lightTarget, Matrix44 lightTransform, ShadowMap* shadowTex, float bias, Vec4 fogColor) {}
void UnbindSolidShader() {}
float RendererGetDeviceTimestamps(unsigned long long* begin, unsigned long long* end, unsigned long long* freq) {return {};}
void* GetGraphicsCommandQueue() {return {};}
void GraphicsTimerBegin() {}
void GraphicsTimerEnd() {}
FluidRenderer* CreateFluidRenderer(uint32_t width, uint32_t height) {return {};}
void DestroyFluidRenderer(FluidRenderer*) {}
FluidRenderBuffers* CreateFluidRenderBuffers(int numParticles, bool enableInterop) {return {};}
void DestroyFluidRenderBuffers(FluidRenderBuffers* buffers) {}
void UpdateFluidRenderBuffers(FluidRenderBuffers* buffers, NvFlexSolver* flex, bool anisotropy, bool density) {}
void UpdateFluidRenderBuffers(FluidRenderBuffers* buffers, 
	Vec4* particles, 
	float* densities, 
	Vec4* anisotropy1, 
	Vec4* anisotropy2, 
	Vec4* anisotropy3, 
	int numParticles, 
	int* indices, 
	int numIndices) {}
DiffuseRenderBuffers* CreateDiffuseRenderBuffers(int numDiffuseParticles, bool& enableInterop) {return {};}
void DestroyDiffuseRenderBuffers(DiffuseRenderBuffers* buffers) {}
void UpdateDiffuseRenderBuffers(DiffuseRenderBuffers* buffers, NvFlexSolver* solver) {}
void UpdateDiffuseRenderBuffers(DiffuseRenderBuffers* buffers,
	Vec4* diffusePositions,
	Vec4* diffuseVelocities,
	int numDiffuseParticles) {}
int GetNumDiffuseRenderParticles(DiffuseRenderBuffers* buffers) {extern int g_maxDiffuseParticles; return g_maxDiffuseParticles;}
void RenderEllipsoids(FluidRenderer* render, FluidRenderBuffers* buffers, int n, int offset, float radius, float screenWidth, float screenAspect, float fov, Vec3 lightPos, Vec3 lightTarget, Matrix44 lightTransform, ShadowMap* shadowTex, Vec4 color, float blur, float ior, bool debug) {}
void RenderDiffuse(FluidRenderer* render, DiffuseRenderBuffers* buffer, int n, float radius, float screenWidth, float screenAspect, float fov, Vec4 color, Vec3 lightPos, Vec3 lightTarget, Matrix44 lightTransform, ShadowMap* shadowTex, float motionBlur,  float inscatter, float outscatter, bool shadow, bool front) {}
void DrawImguiGraph() {}
