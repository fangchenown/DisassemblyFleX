// Generated diagnostic proxy; the runtime DLL does not use or link this file.
struct TracingContext final : NvFlex::Context {
    NvFlex::Context* wrapped; Trace& trace;
    TracingContext(NvFlex::Context* original, Trace& recorder):wrapped(original),trace(recorder){}
    void updateContext(const NvFlexContextDesc* desc) override {
        trace.operation("updateContext");
        wrapped->updateContext(desc);
    }
    ConstantBuffer* createConstantBuffer(const ConstantBufferDesc* desc) override {
        trace.operation("createConstantBuffer");
        auto result=wrapped->createConstantBuffer(desc);
        trace.adopt(result,"created",desc);
        return result;
    }
    void* map(ConstantBuffer* buffer) override {
        trace.operation("map");
        auto result=wrapped->map(buffer);
        trace.mapped(buffer,result);
        return result;
    }
    void unmap(ConstantBuffer* buffer) override {
        trace.capture(buffer);
        trace.operation("unmap");
        wrapped->unmap(buffer);
    }
    void copy(ConstantBuffer* dst, Buffer* src) override {
        trace.operation("copy");
        trace.arguments("copy",{trace.id(dst),trace.id(src)});
        wrapped->copy(dst,src);
    }
    Buffer* createBuffer(const BufferDesc* desc, void* ptr) override {
        trace.operation("createBuffer");
        auto result=wrapped->createBuffer(desc,ptr);
        trace.adopt(result,"created");
        if(result && desc->data) trace.initial(result,desc->data,size_t(desc->dim)*desc->stride);
        return result;
    }
    Buffer* createBufferView(Buffer* buffer, const BufferViewDesc* desc) override {
        trace.operation("createBufferView");
        auto result=wrapped->createBufferView(buffer,desc);
        trace.adopt(result,"created");
        return result;
    }
    void* map(Buffer* buffer, MapType type, bool wait) override {
        trace.operation("map");
        auto result=wrapped->map(buffer,type,wait);
        trace.mapped(buffer,result);
        return result;
    }
    void unmap(Buffer* buffer) override {
        trace.capture(buffer);
        trace.operation("unmap");
        wrapped->unmap(buffer);
    }
    void upload(Buffer* buffer) override {
        trace.operation("upload");
        trace.arguments("upload",{trace.id(buffer)});
        wrapped->upload(buffer);
    }
    void upload(Buffer* buffer, NvFlexUint offset, NvFlexUint numBytes) override {
        trace.operation("upload");
        trace.arguments("upload",{trace.id(buffer),static_cast<unsigned long long>(offset),static_cast<unsigned long long>(numBytes)});
        wrapped->upload(buffer,offset,numBytes);
    }
    void download(Buffer* buffer) override {
        trace.operation("download");
        trace.arguments("download",{trace.id(buffer)});
        wrapped->download(buffer);
    }
    void download(Buffer* buffer, NvFlexUint offset, NvFlexUint numBytes) override {
        trace.operation("download");
        trace.arguments("download",{trace.id(buffer),static_cast<unsigned long long>(offset),static_cast<unsigned long long>(numBytes)});
        wrapped->download(buffer,offset,numBytes);
    }
    void copy(Buffer* dst, unsigned dstByteOffset, Buffer* src, NvFlexUint srcByteOffset, NvFlexUint numBytes) override {
        trace.operation("copy");
        trace.arguments("copy",{trace.id(dst),static_cast<unsigned long long>(dstByteOffset),trace.id(src),static_cast<unsigned long long>(srcByteOffset),static_cast<unsigned long long>(numBytes)});
        wrapped->copy(dst,dstByteOffset,src,srcByteOffset,numBytes);
    }
    void copyToNative(void* dst, unsigned dstByteOffset, Buffer* src, NvFlexUint srcByteOffset, NvFlexUint numBytes) override {
        trace.operation("copyToNative");
        trace.arguments("copyToNative",{trace.id(dst),static_cast<unsigned long long>(dstByteOffset),trace.id(src),static_cast<unsigned long long>(srcByteOffset),static_cast<unsigned long long>(numBytes)});
        wrapped->copyToNative(dst,dstByteOffset,src,srcByteOffset,numBytes);
    }
    void copyToDevice(Buffer* dst, unsigned dstByteOffset, Buffer* src, NvFlexUint srcByteOffset, NvFlexUint numBytes, BufferResourceTypes type) override {
        trace.operation("copyToDevice");
        trace.arguments("copyToDevice",{trace.id(dst),static_cast<unsigned long long>(dstByteOffset),trace.id(src),static_cast<unsigned long long>(srcByteOffset),static_cast<unsigned long long>(numBytes),static_cast<unsigned long long>(type)});
        wrapped->copyToDevice(dst,dstByteOffset,src,srcByteOffset,numBytes,type);
    }
    void copyToHost(Buffer* dst, unsigned dstByteOffset, Buffer* src, NvFlexUint srcByteOffset, NvFlexUint numBytes) override {
        trace.operation("copyToHost");
        trace.arguments("copyToHost",{trace.id(dst),static_cast<unsigned long long>(dstByteOffset),trace.id(src),static_cast<unsigned long long>(srcByteOffset),static_cast<unsigned long long>(numBytes)});
        wrapped->copyToHost(dst,dstByteOffset,src,srcByteOffset,numBytes);
    }
    void clearUnorderedAccessViewUint(Buffer* buffer, const NvFlexUint * values) override {
        trace.operation("clearUnorderedAccessViewUint");
        wrapped->clearUnorderedAccessViewUint(buffer,values);
    }
    void clearUnorderedAccessViewFloat(Buffer* buffer, const NvFlexFloat * values) override {
        trace.operation("clearUnorderedAccessViewFloat");
        wrapped->clearUnorderedAccessViewFloat(buffer,values);
    }
    void copyResourceState(Buffer* bufferFrom, Buffer* bufferTo) override {
        trace.operation("copyResourceState");
        wrapped->copyResourceState(bufferFrom,bufferTo);
    }
    Texture3D* createTexture3D(const Texture3DDesc* desc) override {
        trace.operation("createTexture3D");
        auto result=wrapped->createTexture3D(desc);
        return result;
    }
    MappedData map(Texture3D* buffer) override {
        trace.operation("map");
        auto result=wrapped->map(buffer);
        return result;
    }
    void unmap(Texture3D* buffer) override {
        trace.capture(buffer);
        trace.operation("unmap");
        wrapped->unmap(buffer);
    }
    void download(Texture3D* buffer) override {
        trace.operation("download");
        trace.arguments("download",{trace.id(buffer)});
        wrapped->download(buffer);
    }
    MappedData mapDownload(Texture3D* buffer) override {
        trace.operation("mapDownload");
        auto result=wrapped->mapDownload(buffer);
        return result;
    }
    void unmapDownload(Texture3D* buffer) override {
        trace.capture(buffer);
        trace.operation("unmapDownload");
        wrapped->unmapDownload(buffer);
    }
    void copy(Texture3D* dst, Texture3D* srv) override {
        trace.operation("copy");
        trace.arguments("copy",{trace.id(dst),trace.id(srv)});
        wrapped->copy(dst,srv);
    }
    ComputeShader* createComputeShader(const ComputeShaderDesc* desc) override {
        trace.operation("createComputeShader");
        auto result=wrapped->createComputeShader(desc);
        trace.shader(result);
        return result;
    }
    void dispatch(const DispatchParams* params) override {
        trace.dispatch("dispatch",params);
        wrapped->dispatch(params);
    }
    void dispatchIndirect(const DispatchParams* params) override {
        trace.dispatch("dispatchIndirect",params);
        wrapped->dispatchIndirect(params);
    }
    TimerPool * createTimerPool() override {
        trace.operation("createTimerPool");
        auto result=wrapped->createTimerPool();
        return result;
    }
    Fence* createFence() override {
        trace.operation("createFence");
        auto result=wrapped->createFence();
        return result;
    }
    void fenceSet(Fence * fence) override {
        trace.operation("fenceSet");
        wrapped->fenceSet(fence);
    }
    void fenceWait(Fence * fence) override {
        trace.operation("fenceWait");
        wrapped->fenceWait(fence);
    }
    void startFrame() override {
        trace.operation("startFrame");
        wrapped->startFrame();
    }
    void flush() override {
        trace.operation("flush");
        wrapped->flush();
    }
    void clearState() override {
        trace.operation("clearState");
        wrapped->clearState();
    }
    void computeWaitForGraphics() override {
        trace.operation("computeWaitForGraphics");
        wrapped->computeWaitForGraphics();
    }
    void pixBeginEvent(const wchar_t* label) override {
        trace.operation("pixBeginEvent");
        wrapped->pixBeginEvent(label);
    }
    void pixEndEvent() override {
        trace.operation("pixEndEvent");
        wrapped->pixEndEvent();
    }
    void eventMarker(const wchar_t* label) override {
        trace.operation("eventMarker");
        wrapped->eventMarker(label);
    }
    void contextPush() override {
        trace.operation("contextPush");
        wrapped->contextPush();
    }
    void contextPop() override {
        trace.operation("contextPop");
        wrapped->contextPop();
    }
    int setEventMarkerAftermath(void* markerData, unsigned int markerSize) override {
        trace.operation("setEventMarkerAftermath");
        auto result=wrapped->setEventMarkerAftermath(markerData,markerSize);
        return result;
    }
    int getDataAftermath(GFSDK_Aftermath_ContextData* pContextDataOut, GFSDK_Aftermath_Status* pStatusOut) override {
        trace.operation("getDataAftermath");
        auto result=wrapped->getDataAftermath(pContextDataOut,pStatusOut);
        return result;
    }
};
